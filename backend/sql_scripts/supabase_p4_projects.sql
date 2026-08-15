-- Phase 4: Projects (Initiative, renamed for clarity)
-- Optional containers for organizing research sessions and decisions.
-- All FKs are nullable — research and decisions remain fully functional without a project.

-- 1. Create projects table
CREATE TABLE IF NOT EXISTS public.projects (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id    UUID        NOT NULL REFERENCES public.workspaces(id) ON DELETE CASCADE,
    created_by      TEXT        NOT NULL,   -- user_id (Clerk)
    name            TEXT        NOT NULL,
    description     TEXT,
    status          TEXT        NOT NULL DEFAULT 'active'
                                CHECK (status IN ('active', 'completed', 'archived')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_projects_workspace_id ON public.projects (workspace_id);
CREATE INDEX IF NOT EXISTS idx_projects_created_by   ON public.projects (created_by);
CREATE INDEX IF NOT EXISTS idx_projects_status       ON public.projects (status);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_projects_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_projects_updated_at
    BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION update_projects_updated_at();

-- 2. Add nullable project_id FK to research_sessions
ALTER TABLE public.research_sessions
    ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_research_sessions_project_id ON public.research_sessions (project_id);

-- 3. Add nullable project_id FK to decision_records
ALTER TABLE public.decision_records
    ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES public.projects(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_decision_records_project_id ON public.decision_records (project_id);

-- 4. RLS on projects
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access on projects"
    ON public.projects FOR ALL
    TO service_role
    USING (true) WITH CHECK (true);
