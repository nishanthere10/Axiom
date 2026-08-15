-- 1. Ensure is_active column exists on memory_items
ALTER TABLE public.memory_items
    ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT true;

-- 2. Add last_used_at — tracks when a memory was last injected into a research prompt
ALTER TABLE public.memory_items
    ADD COLUMN IF NOT EXISTS last_used_at TIMESTAMPTZ;

-- 3. Add dedup_hash — SHA-256 of the memory content for deduplication
ALTER TABLE public.memory_items
    ADD COLUMN IF NOT EXISTS dedup_hash TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_memory_items_dedup
    ON public.memory_items (user_id, workspace_id, dedup_hash)
    WHERE dedup_hash IS NOT NULL AND is_active = true;

-- 4. Workspace search: ensure correct indexes exist
-- research_sessions already has workspace_id index from Act 1
-- decision_records already has workspace_id index from Act 1
-- projects already has workspace_id index from Act 1

-- 5. Add FTS index on memory_items.summary for search
CREATE INDEX IF NOT EXISTS idx_memory_items_summary_gin
    ON public.memory_items
    USING gin(to_tsvector('english', summary))
    WHERE is_active = true;

-- 6. Backfill dedup_hash for existing active memories
-- (run in Supabase SQL editor after adding the column)
-- UPDATE memory_items
-- SET dedup_hash = encode(digest(summary, 'sha256'), 'hex')
-- WHERE dedup_hash IS NULL AND is_active = true;
