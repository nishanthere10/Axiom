-- Phase 3: Decision Status History
-- Records every status change on a decision: who changed it, when, and why.
-- This is the "why did this change" audit trail.

CREATE TABLE IF NOT EXISTS public.decision_status_history (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id     UUID        NOT NULL REFERENCES public.decision_records(id) ON DELETE CASCADE,
    from_status     TEXT,                   -- NULL on first creation
    to_status       TEXT        NOT NULL,
    changed_by      TEXT        NOT NULL,   -- user_id (Clerk)
    note            TEXT,                   -- optional reason/context for the change
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_decision_history_decision_id
    ON public.decision_status_history (decision_id);
CREATE INDEX IF NOT EXISTS idx_decision_history_changed_at
    ON public.decision_status_history (changed_at DESC);

-- RLS: service role has full access
ALTER TABLE public.decision_status_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access on decision_status_history"
    ON public.decision_status_history FOR ALL
    TO service_role
    USING (true) WITH CHECK (true);

-- Backfill: create initial history entries for all existing decisions
-- (from_status = NULL, to_status = current status, note = 'backfilled on Phase 3 migration')
INSERT INTO public.decision_status_history (decision_id, from_status, to_status, changed_by, note, changed_at)
SELECT
    id,
    NULL,
    status,
    created_by,
    'Initial record — backfilled during Phase 3 migration',
    created_at
FROM public.decision_records
ON CONFLICT DO NOTHING;
