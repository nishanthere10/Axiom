-- F-013: Decision Records Implementation
-- Run this in Supabase SQL Editor

-- 1. Rename existing table and indexes
ALTER TABLE IF EXISTS public.decision_documents RENAME TO research_reports;

-- Rename indexes if they exist
ALTER INDEX IF EXISTS idx_decision_documents_session RENAME TO idx_research_reports_session;
ALTER INDEX IF EXISTS idx_decision_documents_user_id RENAME TO idx_research_reports_user_id;
ALTER INDEX IF EXISTS idx_decision_documents_workspace_id RENAME TO idx_research_reports_workspace_id;

-- 2. Create the decision_records table
CREATE TABLE IF NOT EXISTS public.decision_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES public.workspaces(id) ON DELETE CASCADE,
    research_session_id UUID NOT NULL REFERENCES public.research_sessions(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PROPOSED', -- PROPOSED, APPROVED, IMPLEMENTED, REJECTED, ARCHIVED
    created_by TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(research_session_id) -- Enforces 1-to-1 mapping
);

CREATE INDEX IF NOT EXISTS idx_decision_records_workspace_id ON public.decision_records(workspace_id);
CREATE INDEX IF NOT EXISTS idx_decision_records_research_session_id ON public.decision_records(research_session_id);
CREATE INDEX IF NOT EXISTS idx_decision_records_status ON public.decision_records(status);

-- 3. Row Level Security
ALTER TABLE public.decision_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage decision records in their workspaces"
ON public.decision_records FOR ALL
USING (
    workspace_id IN (
        SELECT id FROM public.workspaces WHERE user_id = current_setting('request.jwt.claims', true)::json->>'sub'
    )
    OR created_by = current_setting('request.jwt.claims', true)::json->>'sub'
);
