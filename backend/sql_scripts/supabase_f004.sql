-- F-004: Add visuals column to decision_documents
-- Run this in the Supabase SQL Editor

ALTER TABLE public.decision_documents
ADD COLUMN IF NOT EXISTS visuals JSONB DEFAULT '[]'::jsonb,
ADD COLUMN IF NOT EXISTS visual_generated_at TIMESTAMP WITH TIME ZONE;
