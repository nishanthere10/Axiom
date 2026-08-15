-- =============================================================================
-- Production-Grade SQL Migration: Memory Jobs RPC & Schema
-- =============================================================================
-- This migration creates the atomic claim_next_memory_job RPC function and
-- ensures all required columns exist for high-concurrency job processing.
--
-- ISSUE FIXED:
--   - PGRST202: Missing public.claim_next_memory_job RPC function
--   - 42703: Missing columns (status, claimed_at, locked_by, version)
--   - Infinite loop spam from unhandled database errors in memory_sweeper
--
-- EXECUTION:
--   Run this SQL in Supabase SQL Editor or via:
--   $ supabase db push backend/sql/production_memory_jobs_rpc.sql
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- STEP 1: Ensure memory_jobs table exists with required columns
-- ─────────────────────────────────────────────────────────────────────────────

-- Create memory_jobs table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.memory_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    session_id UUID NOT NULL,
    payload JSONB DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    attempt_count INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    last_error TEXT,
    next_retry_at TIMESTAMPTZ,
    workspace_id UUID,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    claimed_at TIMESTAMPTZ,
    locked_by TEXT,
    version INTEGER DEFAULT 1
);

-- ─────────────────────────────────────────────────────────────────────────────
-- STEP 2: Add missing columns (idempotent - IF NOT EXISTS)
-- ─────────────────────────────────────────────────────────────────────────────

ALTER TABLE public.memory_jobs 
ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';

ALTER TABLE public.memory_jobs 
ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ;

ALTER TABLE public.memory_jobs 
ADD COLUMN IF NOT EXISTS locked_by TEXT;

ALTER TABLE public.memory_jobs 
ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;

ALTER TABLE public.memory_jobs 
ADD COLUMN IF NOT EXISTS workspace_id UUID;

-- ─────────────────────────────────────────────────────────────────────────────
-- STEP 3: Create high-performance indexes
-- ─────────────────────────────────────────────────────────────────────────────

-- Index for claiming pending jobs (most common query)
CREATE INDEX IF NOT EXISTS idx_memory_jobs_status_claim 
ON public.memory_jobs (status, created_at) 
WHERE status = 'pending';

-- Index for workspace-scoped queries
CREATE INDEX IF NOT EXISTS idx_memory_jobs_workspace 
ON public.memory_jobs (workspace_id, status, created_at) 
WHERE workspace_id IS NOT NULL;

-- Index for user-scoped queries
CREATE INDEX IF NOT EXISTS idx_memory_jobs_user 
ON public.memory_jobs (user_id, status, created_at);

-- Index for retry queries
CREATE INDEX IF NOT EXISTS idx_memory_jobs_retry 
ON public.memory_jobs (next_retry_at, status) 
WHERE status IN ('failed', 'pending');

-- Index for optimistic locking
CREATE INDEX IF NOT EXISTS idx_memory_jobs_version 
ON public.memory_jobs (id, version, status);

-- ─────────────────────────────────────────────────────────────────────────────
-- STEP 4: Create atomic claim RPC function
-- ─────────────────────────────────────────────────────────────────────────────
-- This function is designed for:
--   - Race condition prevention via SELECT ... FOR UPDATE SKIP LOCKED
--   - Atomic claim + update in a single transaction
--   - Support for workspace isolation (requesting_user_id filter)
--   - Version increment for optimistic locking
--
-- CALL FROM PYTHON:
--   result = supabase.rpc('claim_next_memory_job', {
--       'current_time': datetime.now(timezone.utc).isoformat(),
--       'requesting_user_id': None,  # None = accept any job
--       'worker_id': f'worker_{datetime.now(timezone.utc).timestamp():.6f}'
--   }).execute()
-- ─────────────────────────────────────────────────────────────────────────────

DROP FUNCTION IF EXISTS public.claim_next_memory_job(TIMESTAMPTZ, TEXT, TEXT) CASCADE;

CREATE FUNCTION public.claim_next_memory_job(
    current_time TIMESTAMPTZ,
    requesting_user_id TEXT DEFAULT NULL,
    worker_id TEXT DEFAULT NULL
)
RETURNS SETOF public.memory_jobs
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    next_job_id UUID;
    claimed_job memory_jobs%ROWTYPE;
BEGIN
    -- Step 1: Find the oldest pending job (with locking to prevent race conditions)
    SELECT id INTO next_job_id
    FROM public.memory_jobs
    WHERE status = 'pending'
      AND (requesting_user_id IS NULL OR user_id = requesting_user_id)
    ORDER BY created_at ASC
    FOR UPDATE SKIP LOCKED
    LIMIT 1;

    -- Step 2: If no job found, return empty result set
    IF next_job_id IS NULL THEN
        RETURN;
    END IF;

    -- Step 3: Atomically update the job to mark it as processing
    UPDATE public.memory_jobs j
    SET 
        status = 'processing',
        claimed_at = current_time,
        locked_by = worker_id,
        version = COALESCE(version, 0) + 1,
        updated_at = current_time
    WHERE j.id = next_job_id
    RETURNING j.* INTO claimed_job;

    -- Step 4: Return the updated job
    RETURN NEXT claimed_job;

EXCEPTION WHEN OTHERS THEN
    -- Log the error but don't fail - just return empty result
    RAISE WARNING 'claim_next_memory_job error: %', SQLERRM;
    RETURN;
END;
$$;

-- Grant execute permission to authenticated users and service role
GRANT EXECUTE ON FUNCTION public.claim_next_memory_job(TIMESTAMPTZ, TEXT, TEXT) 
TO authenticated, service_role, anon;

-- ─────────────────────────────────────────────────────────────────────────────
-- STEP 5: Create helper function for updating job status
-- ─────────────────────────────────────────────────────────────────────────────

DROP FUNCTION IF EXISTS public.update_memory_job_status(UUID, TEXT, TEXT) CASCADE;

CREATE FUNCTION public.update_memory_job_status(
    job_id UUID,
    new_status TEXT,
    error_msg TEXT DEFAULT NULL
)
RETURNS SETOF public.memory_jobs
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
    RETURN QUERY
    UPDATE public.memory_jobs
    SET 
        status = new_status,
        last_error = error_msg,
        updated_at = now()
    WHERE id = job_id
    RETURNING *;
EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'update_memory_job_status error: %', SQLERRM;
    RETURN;
END;
$$;

GRANT EXECUTE ON FUNCTION public.update_memory_job_status(UUID, TEXT, TEXT) 
TO authenticated, service_role, anon;

-- ─────────────────────────────────────────────────────────────────────────────
-- STEP 6: Initialize status for existing rows
-- ─────────────────────────────────────────────────────────────────────────────
-- If status column was just added, ensure existing rows have a status

UPDATE public.memory_jobs 
SET status = 'pending' 
WHERE status IS NULL;

UPDATE public.memory_jobs 
SET version = 1 
WHERE version IS NULL;

-- ─────────────────────────────────────────────────────────────────────────────
-- STEP 7: Create trigger to update updated_at timestamp
-- ─────────────────────────────────────────────────────────────────────────────

DROP TRIGGER IF EXISTS update_memory_jobs_updated_at ON public.memory_jobs;

CREATE TRIGGER update_memory_jobs_updated_at
BEFORE UPDATE ON public.memory_jobs
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Helper function for the trigger (if it doesn't exist)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ─────────────────────────────────────────────────────────────────────────────
-- VERIFICATION QUERIES
-- ─────────────────────────────────────────────────────────────────────────────
-- Run these queries to verify the migration succeeded:
--
-- 1. Check that all columns exist:
--    SELECT column_name, data_type FROM information_schema.columns
--    WHERE table_name = 'memory_jobs' ORDER BY column_name;
--
-- 2. Check that indexes exist:
--    SELECT indexname FROM pg_indexes WHERE tablename = 'memory_jobs';
--
-- 3. Test the RPC function:
--    SELECT * FROM public.claim_next_memory_job(
--        now()::TIMESTAMPTZ,
--        NULL::TEXT,
--        'test_worker'::TEXT
--    );
--
-- ─────────────────────────────────────────────────────────────────────────────
-- ROLLBACK (if needed):
-- ─────────────────────────────────────────────────────────────────────────────
-- DROP FUNCTION IF EXISTS public.claim_next_memory_job(TIMESTAMPTZ, TEXT, TEXT);
-- DROP FUNCTION IF EXISTS public.update_memory_job_status(UUID, TEXT, TEXT);
-- ALTER TABLE public.memory_jobs DROP COLUMN IF EXISTS claimed_at;
-- ALTER TABLE public.memory_jobs DROP COLUMN IF EXISTS locked_by;
-- ALTER TABLE public.memory_jobs DROP COLUMN IF EXISTS version;

-- ─────────────────────────────────────────────────────────────────────────────
-- Migration metadata (for tracking)
-- ─────────────────────────────────────────────────────────────────────────────
-- Applied: NOW()
-- Version: 1.0
-- Purpose: Fix PGRST202, 42703 errors and enable high-concurrency memory job claiming
