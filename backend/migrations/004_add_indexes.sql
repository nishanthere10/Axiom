-- 🔐 FIX 6.2: Add Missing Database Indexes
-- Optimize hot query paths for research_sessions, memory_items, research_jobs

-- Research Sessions: workspace queries, status filters
CREATE INDEX IF NOT EXISTS idx_research_sessions_workspace_status 
ON research_sessions(workspace_id, status) 
WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_research_sessions_workspace_created 
ON research_sessions(workspace_id, created_at DESC) 
WHERE deleted_at IS NULL;

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

CREATE INDEX IF NOT EXISTS idx_memory_items_pinned 
ON memory_items(workspace_id, is_pinned) 
WHERE is_pinned = true AND is_active = true;

-- Research Jobs: SSE ticket lookups, status polling
CREATE INDEX IF NOT EXISTS idx_research_jobs_ticket 
ON research_jobs(sse_ticket) 
WHERE sse_ticket IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_research_jobs_session_status 
ON research_jobs(research_session_id, status);

-- Decision Records: workspace dashboard queries
CREATE INDEX IF NOT EXISTS idx_decision_records_workspace_created 
ON decision_records(workspace_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_decision_records_workspace_status 
ON decision_records(workspace_id, status);

-- Comparisons: workspace dashboard queries
CREATE INDEX IF NOT EXISTS idx_comparisons_workspace_created 
ON comparisons(workspace_id, created_at DESC);

-- GitHub Repositories: workspace sync queries
CREATE INDEX IF NOT EXISTS idx_github_repos_workspace_active 
ON github_repositories(workspace_id, is_active) 
WHERE is_active = true;

-- Workspace Members: authorization checks (already likely exists, but ensure)
CREATE INDEX IF NOT EXISTS idx_workspace_members_lookup 
ON workspace_members(workspace_id, user_id);
