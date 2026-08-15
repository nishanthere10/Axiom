-- Add cached_file_paths array to avoid re-fetching github trees on sync
ALTER TABLE github_repositories
    ADD COLUMN IF NOT EXISTS cached_file_paths TEXT[];
