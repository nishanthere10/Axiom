-- Run this in the Supabase SQL Editor

ALTER TABLE public.decision_documents
ADD COLUMN IF NOT EXISTS evidence JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS consensus TEXT DEFAULT '',
ADD COLUMN IF NOT EXISTS evidence_generated_at TIMESTAMP WITH TIME ZONE;
