-- 🔐 FIX 6.2: Add Missing Database Indexes
-- Optimize hot query paths for research_sessions, memory_items, research_jobs
-- Based on actual schema (removed non-existent columns)

-- Research Sessions: workspace queries, status filters
CREATE INDEX IF NOT EXISTS idx_research_sessions_workspace_status 
ON research_sessions(workspace_id, status);

CREATE INDEX IF NOT EXISTS idx_research_sessions_workspace_created 
ON research_sessions(workspace_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_research_sessions_user_created 
ON research_sessions(user_id, created_at DESC);

-- Memory Items: workspace isolation, active filtering, scope queries
CREATE INDEX IF NOT EXISTS idx_memory_items_workspace_active 
ON memory_items(workspace_id, is_active) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_memory_items_user_scope 
ON memory_items(user_id, scope) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_memory_items_dedup_hash 
ON memory_items(dedup_hash, workspace_id, is_active) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_memory_items_user_active 
ON memory_items(user_id, is_active) 
WHERE is_active = true;

-- Research Jobs: session lookups, status polling
CREATE INDEX IF NOT EXISTS idx_research_jobs_session_status 
ON research_jobs(session_id, status);

CREATE INDEX IF NOT EXISTS idx_research_jobs_status_created 
ON research_jobs(status, created_at DESC);

-- Decision Records: workspace dashboard queries
CREATE INDEX IF NOT EXISTS idx_decision_records_workspace_created 
ON decision_records(workspace_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_decision_records_workspace_status 
ON decision_records(workspace_id, status);

CREATE INDEX IF NOT EXISTS idx_decision_records_session 
ON decision_records(research_session_id);

-- Comparisons: workspace dashboard queries
CREATE INDEX IF NOT EXISTS idx_comparisons_workspace_created 
ON comparisons(workspace_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_comparisons_user_created 
ON comparisons(user_id, created_at DESC);

-- GitHub Repositories: workspace sync queries
CREATE INDEX IF NOT EXISTS idx_github_repos_workspace_active 
ON github_repositories(workspace_id, is_active) 
WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_github_repos_user_active 
ON github_repositories(user_id, is_active) 
WHERE is_active = true;

-- Workspace Members: authorization checks
CREATE INDEX IF NOT EXISTS idx_workspace_members_lookup 
ON workspace_members(workspace_id, user_id);

CREATE INDEX IF NOT EXISTS idx_workspace_members_user 
ON workspace_members(user_id);

-- Research Reports: session lookups, workspace filtering
CREATE INDEX IF NOT EXISTS idx_research_reports_session 
ON research_reports(session_id);

CREATE INDEX IF NOT EXISTS idx_research_reports_workspace_created 
ON research_reports(workspace_id, created_at DESC) 
WHERE workspace_id IS NOT NULL;
