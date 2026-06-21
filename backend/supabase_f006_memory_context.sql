-- F-006: Add memory_context column to decision_documents
-- Run this in the Supabase SQL Editor

ALTER TABLE public.decision_documents
ADD COLUMN IF NOT EXISTS memory_context JSONB DEFAULT '{}'::jsonb;
