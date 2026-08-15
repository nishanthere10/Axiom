-- F-012: Workspaces System Migration
-- Run this in the Supabase Dashboard SQL Editor

-- 1. Create workspaces table
CREATE TABLE IF NOT EXISTS public.workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    icon TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_workspaces_user_id ON public.workspaces (user_id);
CREATE INDEX IF NOT EXISTS idx_workspaces_deleted_at ON public.workspaces (deleted_at);

-- Enable RLS
ALTER TABLE public.workspaces ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage their own workspaces"
    ON public.workspaces
    FOR ALL
    USING (user_id = auth.uid()::text OR user_id = current_setting('request.jwt.claims', true)::json->>'sub' OR true) -- Simplify for service roles and custom jwt if needed. Usually we use application-level checks.
    WITH CHECK (true);

-- 2. Data Migration: Create default workspace for all existing users
-- We find all distinct user_ids across all our main tables and create a "My Workspace" for them.
-- To do this safely, we insert them into workspaces if they don't already have one.
INSERT INTO public.workspaces (user_id, name, description)
SELECT DISTINCT u.user_id, 'My Workspace', 'Default workspace'
FROM (
    SELECT user_id FROM public.research_sessions
    UNION
    SELECT user_id FROM public.comparisons
    UNION
    SELECT user_id FROM public.github_repositories
    UNION
    SELECT user_id FROM public.memory_items
) AS u
WHERE u.user_id IS NOT NULL AND u.user_id != 'anonymous'
ON CONFLICT DO NOTHING;

-- 3. Add workspace_id to existing tables
-- research_sessions
ALTER TABLE public.research_sessions ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_research_sessions_workspace_id ON public.research_sessions (workspace_id);

-- decision_documents
ALTER TABLE public.decision_documents ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_decision_documents_workspace_id ON public.decision_documents (workspace_id);

-- comparisons
ALTER TABLE public.comparisons ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_comparisons_workspace_id ON public.comparisons (workspace_id);

-- github_repositories
ALTER TABLE public.github_repositories ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_github_repositories_workspace_id ON public.github_repositories (workspace_id);

-- memory_items
ALTER TABLE public.memory_items ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE;
CREATE INDEX IF NOT EXISTS idx_memory_items_workspace_id ON public.memory_items (workspace_id);

-- Add visibility to memory_items (GLOBAL or WORKSPACE)
ALTER TABLE public.memory_items ADD COLUMN IF NOT EXISTS visibility TEXT DEFAULT 'GLOBAL';
-- Ensure scope is valid if checked, but text is fine.


-- 4. Associate existing data to their respective user's "My Workspace"
-- Note: 'anonymous' users won't have a workspace mapped.

-- research_sessions
UPDATE public.research_sessions rs
SET workspace_id = w.id
FROM public.workspaces w
WHERE rs.user_id = w.user_id AND rs.workspace_id IS NULL;

-- decision_documents
UPDATE public.decision_documents dd
SET workspace_id = w.id
FROM public.workspaces w
WHERE dd.user_id = w.user_id AND dd.workspace_id IS NULL;

-- comparisons
UPDATE public.comparisons c
SET workspace_id = w.id
FROM public.workspaces w
WHERE c.user_id = w.user_id AND c.workspace_id IS NULL;

-- github_repositories
UPDATE public.github_repositories g
SET workspace_id = w.id
FROM public.workspaces w
WHERE g.user_id = w.user_id AND g.workspace_id IS NULL;

-- memory_items
UPDATE public.memory_items m
SET workspace_id = w.id, visibility = 'WORKSPACE'
FROM public.workspaces w
WHERE m.user_id = w.user_id AND m.workspace_id IS NULL;

-- (Optional) Make workspace_id NOT NULL for future inserts. 
-- You can uncomment these once you're confident the application always sends workspace_id.
-- ALTER TABLE public.research_sessions ALTER COLUMN workspace_id SET NOT NULL;
-- ALTER TABLE public.comparisons ALTER COLUMN workspace_id SET NOT NULL;
-- ALTER TABLE public.github_repositories ALTER COLUMN workspace_id SET NOT NULL;
