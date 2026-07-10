CREATE TABLE IF NOT EXISTS public.context_relevance_log (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id           UUID        REFERENCES public.research_sessions(id) ON DELETE CASCADE,
    user_id              TEXT        NOT NULL,
    workspace_id         UUID,
    scored_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Counts
    memories_retrieved   INT         NOT NULL DEFAULT 0,
    memories_injected    INT         NOT NULL DEFAULT 0,
    github_retrieved     INT         NOT NULL DEFAULT 0,
    github_injected      INT         NOT NULL DEFAULT 0,
    total_dropped        INT         NOT NULL DEFAULT 0,

    -- Scores for debugging (best/worst/avg)
    best_memory_score    FLOAT,
    worst_memory_score   FLOAT,
    best_github_score    FLOAT,
    worst_github_score   FLOAT
);

CREATE INDEX IF NOT EXISTS idx_context_relevance_log_session ON context_relevance_log (session_id);
CREATE INDEX IF NOT EXISTS idx_context_relevance_log_user    ON context_relevance_log (user_id);

ALTER TABLE context_relevance_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Service role full access on context_relevance_log"
    ON context_relevance_log FOR ALL TO service_role USING (true) WITH CHECK (true);
