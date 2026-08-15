-- P-001A: Persistent Memory Jobs & Daily Metrics

CREATE TABLE IF NOT EXISTS public.memory_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'queued'
        CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    last_error TEXT,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX idx_memory_jobs_status ON public.memory_jobs(status);
CREATE INDEX idx_memory_jobs_retry ON public.memory_jobs(status, next_retry_at);

-- Add RLS for memory_jobs
ALTER TABLE public.memory_jobs ENABLE ROW LEVEL SECURITY;

-- Allow service role to do everything
CREATE POLICY "Service role can manage memory jobs" 
    ON public.memory_jobs FOR ALL 
    USING (auth.jwt() ->> 'role' = 'service_role');


CREATE TABLE IF NOT EXISTS public.system_metrics_daily (
    date DATE PRIMARY KEY DEFAULT CURRENT_DATE,
    research_count INTEGER DEFAULT 0,
    comparison_count INTEGER DEFAULT 0,
    memory_hit_rate REAL DEFAULT 0.0,
    avg_latency_ms INTEGER DEFAULT 0,
    provider_fallback_count INTEGER DEFAULT 0,
    failed_memory_jobs INTEGER DEFAULT 0
);

ALTER TABLE public.system_metrics_daily ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role can manage metrics" 
    ON public.system_metrics_daily FOR ALL 
    USING (auth.jwt() ->> 'role' = 'service_role');
