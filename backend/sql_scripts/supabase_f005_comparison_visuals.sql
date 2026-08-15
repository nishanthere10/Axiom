-- F-005: Add visuals column to comparisons table
-- Run this in the Supabase SQL Editor

ALTER TABLE public.comparisons
ADD COLUMN IF NOT EXISTS visuals JSONB DEFAULT '[]'::jsonb;
