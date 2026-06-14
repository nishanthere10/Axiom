-- P-001B: Observability & Product Intelligence

-- 1. Create the core append-only events table
CREATE TABLE IF NOT EXISTS analytics_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  event_type TEXT NOT NULL,
  user_id TEXT,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for querying recent events by type
CREATE INDEX IF NOT EXISTS idx_analytics_events_type_time ON analytics_events(event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_analytics_events_time ON analytics_events(created_at DESC);

-- 2. Materialized View: Daily Aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics_daily_mv AS
SELECT
  DATE(created_at) as metric_date,
  COUNT(*) FILTER (WHERE event_type = 'research_completed') as research_count,
  COUNT(*) FILTER (WHERE event_type = 'comparison_completed') as comparison_count,
  COUNT(*) FILTER (WHERE event_type = 'export_requested') as export_count,
  SUM((metadata->>'retrieved_count')::int) FILTER (WHERE event_type = 'memory_retrieved') as memory_retrieval_count,
  COUNT(*) FILTER (WHERE event_type = 'memory_retrieved' AND (metadata->>'hit')::boolean = true) as memory_hit_count,
  COUNT(*) FILTER (WHERE event_type = 'memory_retrieved') as memory_search_count,
  ROUND(AVG((metadata->>'latency_ms')::numeric) FILTER (WHERE event_type = 'research_completed'), 0) as avg_research_latency_ms,
  ROUND(AVG((metadata->>'latency_ms')::numeric) FILTER (WHERE event_type = 'comparison_completed'), 0) as avg_comparison_latency_ms,
  ROUND(AVG((metadata->>'latency_ms')::numeric) FILTER (WHERE event_type = 'memory_retrieved'), 0) as avg_memory_latency_ms,
  COUNT(*) FILTER (WHERE event_type = 'provider_event' AND metadata->>'event' = 'fallback') as provider_fallback_count,
  COUNT(*) FILTER (WHERE event_type = 'memory_job_failed') as failed_memory_jobs
FROM analytics_events
GROUP BY metric_date
ORDER BY metric_date DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_analytics_daily_mv_date ON analytics_daily_mv(metric_date);

-- 3. Materialized View: Provider Metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics_provider_mv AS
SELECT
  DATE(created_at) as metric_date,
  metadata->>'provider' as provider_name,
  COUNT(*) as request_count,
  COUNT(*) FILTER (WHERE metadata->>'event' = 'success') as success_count,
  COUNT(*) FILTER (WHERE metadata->>'event' = 'failure') as failure_count,
  COUNT(*) FILTER (WHERE metadata->>'event' = 'fallback') as fallback_count,
  ROUND(AVG((metadata->>'latency_ms')::numeric), 0) as avg_latency_ms
FROM analytics_events
WHERE event_type = 'provider_event' AND metadata ? 'provider'
GROUP BY metric_date, provider_name
ORDER BY metric_date DESC, provider_name;

CREATE UNIQUE INDEX IF NOT EXISTS idx_analytics_provider_mv_date_name ON analytics_provider_mv(metric_date, provider_name);

-- 4. Materialized View: Topic Metrics
CREATE MATERIALIZED VIEW IF NOT EXISTS analytics_topic_mv AS
SELECT
  DATE(created_at) as metric_date,
  metadata->>'topic' as topic_label,
  COUNT(*) as research_count
FROM analytics_events
WHERE event_type = 'topic_classified' AND metadata ? 'topic'
GROUP BY metric_date, topic_label
ORDER BY metric_date DESC, research_count DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_analytics_topic_mv_date_label ON analytics_topic_mv(metric_date, topic_label);

-- 5. Helper Function to refresh views
CREATE OR REPLACE FUNCTION refresh_analytics_views()
RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY analytics_daily_mv;
  REFRESH MATERIALIZED VIEW CONCURRENTLY analytics_provider_mv;
  REFRESH MATERIALIZED VIEW CONCURRENTLY analytics_topic_mv;
END;
$$ LANGUAGE plpgsql;

-- 6. Setup pg_cron to refresh views automatically (assuming pg_cron extension is active on Supabase)
-- If pg_cron isn't enabled, this will fail gracefully or can be run manually.
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_extension WHERE extname = 'pg_cron'
  ) THEN
    PERFORM cron.schedule('refresh_analytics', '0 * * * *', 'SELECT refresh_analytics_views();');
  END IF;
END
$$;
