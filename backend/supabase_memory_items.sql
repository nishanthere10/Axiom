-- Run this in your Supabase SQL Editor

CREATE TABLE IF NOT EXISTS public.memory_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memory_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_type TEXT NOT NULL,
    summary TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    scope TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMPTZ,
    user_id TEXT NOT NULL DEFAULT 'anonymous',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_items_user_id ON public.memory_items (user_id);
CREATE INDEX IF NOT EXISTS idx_memory_items_is_active ON public.memory_items (is_active);

-- Enable RLS
ALTER TABLE public.memory_items ENABLE ROW LEVEL SECURITY;

-- Allow service role full access
CREATE POLICY "Enable ALL for service-role on memory_items" ON public.memory_items
    AS PERMISSIVE FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
