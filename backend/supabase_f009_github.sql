-- F-009 GitHub Context Provider Tables

-- Connection Table
CREATE TABLE IF NOT EXISTS github_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL UNIQUE,
    github_user_id TEXT,
    github_username TEXT,
    encrypted_access_token TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_github_connections_user_id ON github_connections(user_id);

-- Repositories Table
CREATE TABLE IF NOT EXISTS github_repositories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    repository_name TEXT NOT NULL,
    repository_owner TEXT NOT NULL,
    repository_url TEXT NOT NULL,
    is_private BOOLEAN DEFAULT false,
    is_active BOOLEAN DEFAULT false,
    last_synced_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, repository_id)
);

CREATE INDEX IF NOT EXISTS idx_github_repositories_user_id ON github_repositories(user_id);

-- Sync Jobs Table
CREATE TABLE IF NOT EXISTS github_sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued', -- queued, running, completed, failed
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_github_sync_jobs_user_id ON github_sync_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_github_sync_jobs_repository_id ON github_sync_jobs(repository_id);

-- RLS Policies (assuming standard Atlas setup where user_id manages their own data)
ALTER TABLE github_connections ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own github connections" ON github_connections FOR ALL USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub');

ALTER TABLE github_repositories ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own github repositories" ON github_repositories FOR ALL USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub');

ALTER TABLE github_sync_jobs ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can manage their own sync jobs" ON github_sync_jobs FOR ALL USING (user_id = current_setting('request.jwt.claims', true)::json->>'sub');
