-- F-010: GitHub Sync Progress & Path Selection
-- Run this in Supabase SQL Editor after supabase_f009_github.sql

-- Add progress tracking and path selection to sync jobs
ALTER TABLE github_sync_jobs
    ADD COLUMN IF NOT EXISTS progress_current INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS progress_total INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_file TEXT,
    ADD COLUMN IF NOT EXISTS selected_paths TEXT[];

-- Add selected_paths cache to repositories (re-use on next sync without re-picking)
ALTER TABLE github_repositories
    ADD COLUMN IF NOT EXISTS selected_paths TEXT[];
