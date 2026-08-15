-- Migration: Add columns for atomic job claiming
-- Run this migration to add required fields for race-condition-free job processing

-- Add version column for optimistic locking
ALTER TABLE memory_jobs 
ADD COLUMN IF NOT EXISTS version INTEGER DEFAULT 0;

-- Add claimed tracking columns
ALTER TABLE memory_jobs 
ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ;

ALTER TABLE memory_jobs 
ADD COLUMN IF NOT EXISTS claimed_by TEXT;

-- Create index for efficient job claiming
CREATE INDEX IF NOT EXISTS idx_memory_jobs_claim 
ON memory_jobs (status, next_retry_at, claimed_at) 
WHERE status IN ('queued', 'failed');

-- Create index for version-based optimistic locking
CREATE INDEX IF NOT EXISTS idx_memory_jobs_version 
ON memory_jobs (id, version, status);

-- Update existing jobs to have version 0
UPDATE memory_jobs 
SET version = 0 
WHERE version IS NULL;