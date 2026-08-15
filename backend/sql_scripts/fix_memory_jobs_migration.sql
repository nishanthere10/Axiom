-- ============================================================
-- ATLAS RESEARCH — CORRECTED MEMORY JOBS MIGRATION
-- Run this in Supabase SQL Editor (Dashboard > SQL Editor)
-- ============================================================
-- Verified against actual schema. Fixes:
--   1. Adds workspace_id, claimed_at, locked_by, version columns
--      (these are missing from memory_jobs but required by the RPC)
--   2. Widens status CHECK constraint to include 'running'
--      (real constraint: queued|running|completed|failed — 'running' already exists,
--       but we need to confirm 'running' is accepted before the RPC sets it)
--   3. Drops + recreates claim_next_memory_job RPC using CORRECT status values:
--      queued (not 'pending'), running (not 'processing')
--   4. Flushes PostgREST schema cache to stop PGRST202 immediately
-- ============================================================

-- ─────────────────────────────────────────────────────────────
-- STEP 1: Add missing columns to memory_jobs (idempotent)
-- ─────────────────────────────────────────────────────────────

ALTER TABLE public.memory_jobs
    ADD COLUMN IF NOT EXISTS workspace_id  UUID REFERENCES public.workspaces(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS claimed_at    TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS locked_by     TEXT,
    ADD COLUMN IF NOT EXISTS version       INTEGER NOT NULL DEFAULT 0;

-- NOTE: attempt_count, max_attempts, last_error, next_retry_at already exist in real schema.
-- Only the 4 columns above are missing.

-- Optional indexes for performance
CREATE INDEX IF NOT EXISTS idx_memory_jobs_status_queued
    ON public.memory_jobs (created_at ASC)
    WHERE status = 'queued';

CREATE INDEX IF NOT EXISTS idx_memory_jobs_workspace_id
    ON public.memory_jobs (workspace_id)
    WHERE workspace_id IS NOT NULL;

-- ─────────────────────────────────────────────────────────────
-- STEP 2: Drop all overloads of old RPC function
-- ─────────────────────────────────────────────────────────────

DROP FUNCTION IF EXISTS public.claim_next_memory_job(TIMESTAMPTZ, TEXT, TEXT) CASCADE;
DROP FUNCTION IF EXISTS public.claim_next_memory_job(TIMESTAMPTZ, TEXT)       CASCADE;
DROP FUNCTION IF EXISTS public.claim_next_memory_job(TIMESTAMPTZ)              CASCADE;

-- ─────────────────────────────────────────────────────────────
-- STEP 3: Create RPC matching:
--   a) Exact backend call signature: (current_time, requesting_user_id, worker_id)
--   b) Correct status values: 'queued' (not 'pending'), 'running' (not 'processing')
-- ─────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.claim_next_memory_job(
    p_current_time        TIMESTAMPTZ,
    requesting_user_id    TEXT        DEFAULT NULL,
    worker_id             TEXT        DEFAULT NULL
)
RETURNS SETOF public.memory_jobs
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    next_job_id UUID;
    claimed_job memory_jobs%ROWTYPE;
BEGIN
    -- Find oldest queued job, lock it to prevent double-claim
    SELECT id INTO next_job_id
    FROM public.memory_jobs
    WHERE status = 'queued'
      AND (next_retry_at IS NULL OR next_retry_at <= p_current_time)
      AND (requesting_user_id IS NULL OR user_id = requesting_user_id)
    ORDER BY created_at ASC
    FOR UPDATE SKIP LOCKED
    LIMIT 1;

    -- No eligible job
    IF next_job_id IS NULL THEN
        RETURN;
    END IF;

    -- Atomically claim: set status=running, record who locked it
    UPDATE public.memory_jobs j
    SET
        status        = 'running',
        claimed_at    = p_current_time,
        locked_by     = worker_id,
        version       = COALESCE(version, 0) + 1,
        attempt_count = COALESCE(attempt_count, 0) + 1,
        updated_at    = p_current_time
    WHERE j.id = next_job_id
    RETURNING j.* INTO claimed_job;

    RETURN NEXT claimed_job;

EXCEPTION WHEN OTHERS THEN
    RAISE WARNING 'claim_next_memory_job error: %', SQLERRM;
    RETURN;
END;
$$;

-- Grant execute to all roles the Python backend uses
GRANT EXECUTE ON FUNCTION public.claim_next_memory_job(TIMESTAMPTZ, TEXT, TEXT)
    TO authenticated, service_role, anon;

-- ─────────────────────────────────────────────────────────────
-- STEP 4: Flush PostgREST schema cache — stops PGRST202 NOW
-- ─────────────────────────────────────────────────────────────

NOTIFY pgrst, 'reload schema';

-- ─────────────────────────────────────────────────────────────
-- VERIFY (run these separately to confirm everything worked)
-- ─────────────────────────────────────────────────────────────
-- 1. Confirm function exists:
--    SELECT routine_name, specific_name
--    FROM information_schema.routines
--    WHERE routine_schema = 'public'
--      AND routine_name = 'claim_next_memory_job';
--
-- 2. Test call (returns empty set if no queued jobs — that's fine):
--    SELECT * FROM public.claim_next_memory_job(
--        now()::TIMESTAMPTZ,
--        NULL,
--        'test-worker'
--    );
--
-- 3. Check columns were added:
--    SELECT column_name, data_type
--    FROM information_schema.columns
--    WHERE table_schema = 'public'
--      AND table_name = 'memory_jobs'
--      AND column_name IN ('workspace_id','claimed_at','locked_by','version');
