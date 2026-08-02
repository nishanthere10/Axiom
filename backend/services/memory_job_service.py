import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from services.db import get_supabase

logger = logging.getLogger(__name__)

class MemoryJobServiceError(Exception):
    """Base exception for memory job service errors."""
    pass

class DatabaseError(MemoryJobServiceError):
    """Raised when database operations fail."""
    pass

def create_job(user_id: str, session_id: str, payload: Dict[str, Any]) -> str:
    """
    Creates a new memory job in the pending state.
    
    SECURITY FIX: Enforces workspace isolation by storing workspace_id.
    Raises ValueError if user doesn't have access to the workspace.
    """
    supabase = get_supabase("worker")
    
    # Extract and validate workspace_id from payload
    workspace_id = payload.get("workspace_id")
    if workspace_id:
        # Verify user has access to this workspace
        try:
            workspace_check = supabase.table("workspace_members")\
                .select("id")\
                .eq("workspace_id", workspace_id)\
                .eq("user_id", user_id)\
                .execute()
            
            if not workspace_check.data:
                raise ValueError(f"User {user_id} does not have access to workspace {workspace_id}")
        except Exception as e:
            logger.error(f"Workspace verification failed: {e}")
            raise ValueError(f"Invalid workspace access: {e}")
    
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "payload": payload,
        "status": "queued",  # Matches DB CHECK constraint: queued|running|completed|failed
        "attempt_count": 0,
        "workspace_id": workspace_id,
        "max_attempts": 3
    }
    
    try:
        result = supabase.table("memory_jobs").insert(data).execute()
        job_id = result.data[0]["id"]
        logger.info(f"Created memory job {job_id} for session {session_id} in workspace {workspace_id}")
        return job_id
    except Exception as e:
        logger.error(f"Failed to create memory job: {e}")
        raise DatabaseError(f"Failed to create memory job: {e}")

def claim_next_job() -> Optional[Dict[str, Any]]:
    """
    PRODUCTION FIX: Atomically finds and claims the oldest eligible job.
    
    APPROACH:
      1. Try atomic RPC call (claim_next_memory_job) first - no race conditions
      2. If RPC fails (PGRST202 or other error), fall back to safe query method
      3. Return None on any error rather than raising exception to prevent sweeper crash
    
    RETURNS:
      Claimed job dict if successful, None if no jobs or all errors handled gracefully.
    
    ERRORS HANDLED:
      - PGRST202: RPC function not found (fallback to safe query)
      - 42703: Missing column (handled by defensive fallback)
      - Network errors: Logged, returns None
      - Other Supabase errors: Logged, returns None
    """
    supabase = get_supabase("worker")
    now = datetime.now(timezone.utc).isoformat()
    worker_id = f"worker_{datetime.now(timezone.utc).timestamp():.6f}"
    
    # ─────────────────────────────────────────────────────────────────────────
    # ATTEMPT 1: Use atomic RPC function (preferred, no race conditions)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        logger.debug(f"Attempting atomic RPC claim with worker_id={worker_id}")
        result = supabase.rpc('claim_next_memory_job', {
            'current_time': now,
            'worker_id': worker_id,
            'requesting_user_id': None
        }).execute()
        
        if result.data and len(result.data) > 0:
            claimed_job = result.data[0]
            workspace_id = claimed_job.get("workspace_id", "global")
            logger.info(
                f"✓ Claimed memory job {claimed_job['id']} by worker {worker_id} "
                f"for workspace {workspace_id} [RPC SUCCESS]"
            )
            return claimed_job
        else:
            logger.debug("No pending jobs available [RPC SUCCESS - no jobs]")
            return None
            
    except Exception as rpc_error:
        error_str = str(rpc_error).lower()
        
        # PGRST202 = RPC function not found, try fallback
        if "pgrst202" in error_str or "function" in error_str:
            logger.warning(
                f"RPC function not available (PGRST202 or similar), falling back to safe query: {rpc_error}"
            )
            return _claim_next_job_fallback_safe(now, worker_id)
        
        # Other errors: log and try fallback
        logger.warning(
            f"RPC claim_next_memory_job failed ({type(rpc_error).__name__}), "
            f"falling back to safe query: {rpc_error}"
        )
        return _claim_next_job_fallback_safe(now, worker_id)

def _claim_next_job_fallback_safe(now: str, worker_id: str) -> Optional[Dict[str, Any]]:
    """
    PRODUCTION FIX: Safe fallback that only queries standard columns.
    
    Handles missing columns gracefully:
      - Only queries: id, status, created_at, updated_at, user_id, session_id, payload
      - Does NOT query: version, claimed_at, locked_by (which may not exist)
      - Returns None if query fails (prevents infinite loop crashes)
    
    STRATEGY:
      1. Query only safe standard columns (created_at, status, user_id, session_id, payload)
      2. Sort by created_at (oldest first)
      3. Add jitter to reduce collision probability
      4. Attempt update with basic WHERE clauses (no version check)
      5. Return None on any error (caller will retry after sleep)
    """
    supabase = get_supabase("worker")
    
    # Add random jitter to reduce collision probability
    import random
    import time
    time.sleep(random.uniform(0, 0.1))  # 0-100ms jitter
    
    try:
        # ─────────────────────────────────────────────────────────────────────
        # STEP 1: Query only safe, standard columns
        # ─────────────────────────────────────────────────────────────────────
        logger.debug("Querying for pending jobs (fallback method)")
        
        query = supabase.table("memory_jobs")\
            .select("id, status, created_at, updated_at, user_id, session_id, payload")\
            .eq("status", "queued")\
            .order("created_at", desc=False)\
            .limit(1)
        
        result = query.execute()
        if not result.data or len(result.data) == 0:
            logger.debug("No pending jobs available [FALLBACK - no jobs]")
            return None
        
        job = result.data[0]
        job_id = job["id"]
        
        logger.debug(f"Found pending job {job_id}, attempting to claim [FALLBACK]")
        
        # ─────────────────────────────────────────────────────────────────────
        # STEP 2: Attempt update with basic WHERE clauses
        # ─────────────────────────────────────────────────────────────────────
        # Use only standard columns for the update conditions
        update_payload = {
            "status": "running",  # Matches DB CHECK constraint
            "updated_at": now
        }
        
        claim_result = supabase.table("memory_jobs")\
            .update(update_payload)\
            .eq("id", job_id)\
            .eq("status", "queued")\
            .execute()
        
        if claim_result.data and len(claim_result.data) > 0:
            logger.info(
                f"✓ Claimed memory job {job_id} by worker {worker_id} "
                f"[FALLBACK SUCCESS]"
            )
            return claim_result.data[0]
        else:
            logger.debug(
                f"Failed to claim job {job_id} - already claimed by another worker "
                f"[FALLBACK - race loss]"
            )
            return None
            
    except Exception as e:
        # CRITICAL: Do not raise - return None so sweeper can sleep and retry
        logger.error(
            f"Fallback job claiming failed ({type(e).__name__}): {e} "
            f"[FALLBACK ERROR - returning None]"
        )
        return None

def complete_job(job_id: str) -> None:
    """Marks a job as completed."""
    supabase = get_supabase("worker")
    try:
        supabase.table("memory_jobs").update({
            "status": "completed",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }).eq("id", job_id).execute()
        logger.info(f"Completed memory job {job_id}")
    except Exception as e:
        logger.error(f"Failed to mark job {job_id} as completed: {e}")
        # Don't raise - this is non-critical

def fail_job(job_id: str, attempt_count: int, max_attempts: int, error_message: str) -> None:
    """
    Marks a job as failed and schedules retry if eligible.
    
    Backoff schedule:
      - Attempt 1 → retry after 30s
      - Attempt 2+ → retry after 120s
      - After max_attempts → permanent failure (no retry)
    """
    supabase = get_supabase("worker")
    new_attempt = attempt_count + 1
    
    try:
        if new_attempt >= max_attempts:
            # Permanent failure
            logger.error(
                f"Memory job {job_id} permanently failed after {new_attempt} attempts. "
                f"Error: {error_message}"
            )
            supabase.table("memory_jobs").update({
                "status": "failed",
                "attempt_count": new_attempt,
                "last_error": error_message,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", job_id).execute()
            
            # Record in metrics
            try:
                from services.metrics_service import increment_failed_memory_jobs
                increment_failed_memory_jobs()
            except Exception:
                pass  # Ignore metrics errors
        else:
            # Schedule retry
            backoff_seconds = 30 if new_attempt == 1 else 120
            next_retry = (datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)).isoformat()
            
            logger.warning(
                f"Memory job {job_id} failed (attempt {new_attempt}/{max_attempts}). "
                f"Retrying at {next_retry}. Error: {error_message}"
            )
            supabase.table("memory_jobs").update({
                "status": "queued",  # Reset to queued for retry (matches DB constraint)
                "attempt_count": new_attempt,
                "last_error": error_message,
                "next_retry_at": next_retry,  # Use dedicated retry column
                "updated_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", job_id).execute()
            
    except Exception as e:
        logger.error(f"Failed to update job {job_id} failure status: {e}")
        # Don't raise - sweeper should continue

