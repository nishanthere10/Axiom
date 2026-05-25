-- Run this in the Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_a UUID NOT NULL REFERENCES public.decision_documents(id) ON DELETE CASCADE,
    session_b UUID NOT NULL REFERENCES public.decision_documents(id) ON DELETE CASCADE,
    summary TEXT,
    structural_diff JSONB NOT NULL DEFAULT '{}'::jsonb,
    decision_evolution TEXT NOT NULL DEFAULT '',
    impact_summary TEXT NOT NULL DEFAULT '',
    saved BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS (Service Role access only by default)
ALTER TABLE public.comparisons ENABLE ROW LEVEL SECURITY;

-- Ensure service_role has full access
CREATE POLICY "Enable ALL for service-role on comparisons" ON public.comparisons
    AS PERMISSIVE FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
