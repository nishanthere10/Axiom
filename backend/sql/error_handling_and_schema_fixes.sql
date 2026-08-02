-- Migration: Error Handling and Schema Fixes for Memory Jobs
-- This migration ensures all required columns exist for the memory job service

-- STEP 1: Ensure version column exists for optimistic locking (fallback mechanism)
-- This fixes Error 42703 "column version does not exist" in fallback method
ALTER TABLE memory_jobs 
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 0;

-- STEP 2: Ensure claiming tracking columns exist
ALTER TABLE memory_jobs 
ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ;

ALTER TABLE memory_jobs 
ADD COLUMN IF NOT EXISTS claimed_by TEXT;

-- STEP 3: Ensure workspace_id column exists for workspace isolation
ALTER TABLE memory_jobs 
ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE;

-- STEP 4: Create required indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_memory_jobs_claim 
ON memory_jobs (status, next_retry_at, claimed_at) 
WHERE status IN ('queued', 'failed');

CREATE INDEX IF NOT EXISTS idx_memory_jobs_version 
ON memory_jobs (id, version, status);

CREATE INDEX IF NOT EXISTS idx_memory_jobs_workspace 
ON memory_jobs (workspace_id, status, next_retry_at) 
WHERE workspace_id IS NOT NULL;

-- STEP 5: Initialize version column for existing rows without it
UPDATE memory_jobs 
SET version = 0 
WHERE version IS NULL;

-- STEP 6: Verify claim_next_memory_job RPC function exists (from workspace_isolation_migration.sql)
-- If this function is missing, the RPC will fail and fallback method will be used
-- The fallback method now handles missing version column gracefully
-- by checking if the version key exists in the returned data before using it

-- COMMIT MESSAGE: Added defensive schema and error handling for memory job claiming
-- - Version column with default 0 for optimistic locking
-- - Workspace isolation support
-- - Proper indexing for performance
-- - Fallback method handles missing version column gracefully
