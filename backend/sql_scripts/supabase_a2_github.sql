-- Phase 8: Repository Intelligence Upgrade
-- Run this in Supabase SQL Editor

-- 1. Add new columns to github_repositories
ALTER TABLE public.github_repositories
    ADD COLUMN IF NOT EXISTS file_hashes        JSONB       DEFAULT '{}'::jsonb,
    ADD COLUMN IF NOT EXISTS webhook_id         TEXT,
    ADD COLUMN IF NOT EXISTS webhook_secret     TEXT,
    ADD COLUMN IF NOT EXISTS last_sync_at       TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS indexed_file_count INT         DEFAULT 0,
    ADD COLUMN IF NOT EXISTS total_file_count   INT         DEFAULT 0,
    ADD COLUMN IF NOT EXISTS workspace_id       UUID        REFERENCES public.workspaces(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_github_repos_workspace ON public.github_repositories (workspace_id);

-- 2. Repository profile: rich tech stack + architecture summary
CREATE TABLE IF NOT EXISTS public.github_repository_profiles (
    id                      UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id           UUID        NOT NULL UNIQUE REFERENCES public.github_repositories(id) ON DELETE CASCADE,
    workspace_id            UUID,
    tech_stack              JSONB       DEFAULT '[]'::jsonb,
    architecture_patterns   JSONB       DEFAULT '[]'::jsonb,
    architecture_summary    TEXT,
    key_files               JSONB       DEFAULT '[]'::jsonb,
    primary_language        TEXT,
    last_commit_at          TIMESTAMPTZ,
    generated_at            TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.github_repository_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access on github_repository_profiles"
    ON public.github_repository_profiles FOR ALL TO service_role USING (true) WITH CHECK (true);

-- 3. Sync history log
CREATE TABLE IF NOT EXISTS public.github_sync_log (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id   UUID        NOT NULL REFERENCES public.github_repositories(id) ON DELETE CASCADE,
    user_id         TEXT        NOT NULL,
    trigger         TEXT        NOT NULL,   -- 'manual' | 'webhook' | 'scheduled'
    files_added     INT         DEFAULT 0,
    files_updated   INT         DEFAULT 0,
    files_deleted   INT         DEFAULT 0,
    files_total     INT         DEFAULT 0,
    duration_ms     INT,
    success         BOOLEAN     DEFAULT true,
    error_message   TEXT,
    started_at      TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.github_sync_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access on github_sync_log"
    ON public.github_sync_log FOR ALL TO service_role USING (true) WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_github_sync_log_repo ON public.github_sync_log (repository_id, started_at DESC);
