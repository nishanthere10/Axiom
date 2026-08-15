-- SECURITY FIX: Enhanced workspace isolation for memory jobs
-- Adds constraints and indexes to prevent cross-workspace data leakage

-- Add workspace_id column to memory_jobs if not exists
ALTER TABLE memory_jobs 
ADD COLUMN IF NOT EXISTS workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE;

-- Create index for workspace-scoped job queries
CREATE INDEX IF NOT EXISTS idx_memory_jobs_workspace 
ON memory_jobs (workspace_id, status, next_retry_at) 
WHERE workspace_id IS NOT NULL;

-- Create index for user-scoped job queries (for global/personal jobs)
CREATE INDEX IF NOT EXISTS idx_memory_jobs_user_global 
ON memory_jobs (user_id, status, next_retry_at) 
WHERE workspace_id IS NULL;

-- Ensure workspace_members has proper constraints for memory isolation
-- (This should already exist, but we're being defensive)
CREATE INDEX IF NOT EXISTS idx_workspace_members_lookup 
ON workspace_members (workspace_id, user_id);

-- Add constraint to prevent cross-workspace memory job access
-- This ensures jobs can only be processed by users who have access to the workspace
CREATE OR REPLACE FUNCTION check_memory_job_workspace_access()
RETURNS TRIGGER AS $$
BEGIN
    -- If workspace_id is set, ensure user has access to that workspace
    IF NEW.workspace_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1 FROM workspace_members 
            WHERE workspace_id = NEW.workspace_id 
            AND user_id = NEW.user_id
        ) THEN
            RAISE EXCEPTION 'User does not have access to workspace % for memory job', NEW.workspace_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply the constraint trigger
DROP TRIGGER IF EXISTS memory_job_workspace_access_trigger ON memory_jobs;
CREATE TRIGGER memory_job_workspace_access_trigger
    BEFORE INSERT OR UPDATE ON memory_jobs
    FOR EACH ROW
    EXECUTE FUNCTION check_memory_job_workspace_access();

-- Update the atomic claiming function to respect workspace isolation
CREATE OR REPLACE FUNCTION claim_next_memory_job(
    current_time timestamptz,
    worker_id text,
    requesting_user_id text DEFAULT NULL
) 
RETURNS SETOF memory_jobs
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    claimed_job memory_jobs%ROWTYPE;
BEGIN
    -- Use FOR UPDATE SKIP LOCKED for true atomic claiming
    -- SECURITY FIX: Add workspace access check to job claiming
    SELECT mj.* INTO claimed_job
    FROM memory_jobs mj
    LEFT JOIN workspace_members wm ON mj.workspace_id = wm.workspace_id
    WHERE mj.status IN ('queued', 'failed')
      AND mj.next_retry_at <= current_time
      AND (mj.claimed_at IS NULL OR mj.claimed_at < current_time - INTERVAL '10 minutes') -- Recover stale claims
      AND (
          -- Allow global jobs (no workspace_id)
          mj.workspace_id IS NULL 
          OR 
          -- Allow workspace jobs only if user has access (or no user filter)
          (requesting_user_id IS NULL OR (wm.user_id = requesting_user_id AND wm.user_id = mj.user_id))
      )
    ORDER BY mj.next_retry_at ASC
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
GRANT EXECUTE ON FUNCTION claim_next_memory_job(timestamptz, text, text) TO authenticated;
GRANT EXECUTE ON FUNCTION claim_next_memory_job(timestamptz, text, text) TO service_role;