-- P-001: Add user_id column to all user-owned tables
-- Run this in the Supabase Dashboard SQL Editor
-- Backward compatible: existing rows get 'anonymous' as user_id

-- 1. research_sessions
ALTER TABLE public.research_sessions
ADD COLUMN IF NOT EXISTS user_id TEXT NOT NULL DEFAULT 'anonymous';

CREATE INDEX IF NOT EXISTS idx_research_sessions_user_id
ON public.research_sessions (user_id);

-- 2. decision_documents
ALTER TABLE public.decision_documents
ADD COLUMN IF NOT EXISTS user_id TEXT NOT NULL DEFAULT 'anonymous';

CREATE INDEX IF NOT EXISTS idx_decision_documents_user_id
ON public.decision_documents (user_id);

-- 3. comparisons
ALTER TABLE public.comparisons
ADD COLUMN IF NOT EXISTS user_id TEXT NOT NULL DEFAULT 'anonymous';

CREATE INDEX IF NOT EXISTS idx_comparisons_user_id
ON public.comparisons (user_id);

-- 4. memory_items
ALTER TABLE public.memory_items
ADD COLUMN IF NOT EXISTS user_id TEXT NOT NULL DEFAULT 'anonymous';

CREATE INDEX IF NOT EXISTS idx_memory_items_user_id
ON public.memory_items (user_id);
