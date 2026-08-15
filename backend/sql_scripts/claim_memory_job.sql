-- SECURITY FIX: Atomic job claiming function to prevent race conditions
-- This function uses FOR UPDATE SKIP LOCKED to safely claim jobs in concurrent environment

CREATE OR REPLACE FUNCTION claim_next_memory_job(
    current_time timestamptz,
    worker_id text
) 
RETURNS SETOF memory_jobs
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    claimed_job memory_jobs%ROWTYPE;
BEGIN
    -- Use FOR UPDATE SKIP LOCKED for true atomic claiming
    -- This prevents deadlocks and ensures only one worker can claim each job
    SELECT * INTO claimed_job
    FROM memory_jobs
    WHERE status IN ('queued', 'failed')
      AND next_retry_at <= current_time
      AND (claimed_at IS NULL OR claimed_at < current_time - INTERVAL '10 minutes') -- Recover stale claims
    ORDER BY next_retry_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED;

    -- If no job found, return empty result
    IF NOT FOUND THEN
        RETURN;
    END IF;

    -- Atomically update the job status
    UPDATE memory_jobs 
    SET 
        status = 'running',
        updated_at = current_time,
        claimed_at = current_time,
        claimed_by = worker_id,
        version = COALESCE(version, 0) + 1
    WHERE id = claimed_job.id;

    -- Return the claimed job
    SELECT * INTO claimed_job FROM memory_jobs WHERE id = claimed_job.id;
    RETURN NEXT claimed_job;
    
    RETURN;
END;
$$;

-- Grant execution permissions
GRANT EXECUTE ON FUNCTION claim_next_memory_job(timestamptz, text) TO authenticated;
GRANT EXECUTE ON FUNCTION claim_next_memory_job(timestamptz, text) TO service_role;