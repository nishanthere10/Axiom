import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from services.db import get_supabase

logger = logging.getLogger(__name__)

def create_job(user_id: str, session_id: str, payload: Dict[str, Any]) -> str:
    """Creates a new memory job in the queued state."""
    supabase = get_supabase()
    data = {
        "user_id": user_id,
        "session_id": session_id,
        "payload": payload,
        "status": "queued",
        "attempt_count": 0,
        "next_retry_at": datetime.utcnow().isoformat()
    }
    
    result = supabase.table("memory_jobs").insert(data).execute()
    job_id = result.data[0]["id"]
    logger.info(f"Created memory job {job_id} for session {session_id}")
    return job_id

def claim_next_job() -> Optional[Dict[str, Any]]:
    """
    Finds the oldest eligible job and marks it as running.
    In a high-concurrency Postgres setup, you'd use FOR UPDATE SKIP LOCKED.
    Since we use Supabase REST API, we do a simple select and atomic update.
    """
    supabase = get_supabase()
    now = datetime.utcnow().isoformat()
    
    # Get oldest job that is either queued, or failed and ready for retry
    query = supabase.table("memory_jobs")\
        .select("*")\
        .in_("status", ["queued", "failed"])\
        .lte("next_retry_at", now)\
        .order("next_retry_at")\
        .limit(1)
        
    result = query.execute()
    if not result.data:
        return None
        
    job = result.data[0]
    job_id = job["id"]
    
    # Atomically try to claim it
    claim_result = supabase.table("memory_jobs")\
        .update({"status": "running", "updated_at": datetime.utcnow().isoformat()})\
        .eq("id", job_id)\
        .in_("status", ["queued", "failed"])\
        .execute()
        
    if claim_result.data:
        return claim_result.data[0]
        
    return None # Someone else claimed it

def complete_job(job_id: str) -> None:
    """Marks a job as completed."""
    supabase = get_supabase()
    supabase.table("memory_jobs").update({
        "status": "completed",
        "updated_at": datetime.utcnow().isoformat()
    }).eq("id", job_id).execute()
    logger.info(f"Completed memory job {job_id}")

def fail_job(job_id: str, attempt_count: int, max_attempts: int, error_message: str) -> None:
    """
    Marks a job as failed, scheduling a retry if eligible.
    Backoff schedule: attempt 1 -> +30s, attempt 2 -> +120s
    """
    supabase = get_supabase()
    new_attempt = attempt_count + 1
    
    if new_attempt >= max_attempts:
        # Permanent failure
        logger.error(f"Memory job {job_id} permanently failed after {new_attempt} attempts: {error_message}")
        supabase.table("memory_jobs").update({
            "status": "failed",
            "attempt_count": new_attempt,
            "last_error": error_message,
            "next_retry_at": None, # Never retry again
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", job_id).execute()
        
        # Also record in metrics
        try:
            from services.metrics_service import increment_failed_memory_jobs
            increment_failed_memory_jobs()
        except Exception:
            pass # Ignore if metrics service not ready
    else:
        # Schedule retry
        backoff_seconds = 30 if new_attempt == 1 else 120
        next_retry = (datetime.utcnow() + timedelta(seconds=backoff_seconds)).isoformat()
        
        logger.warning(f"Memory job {job_id} failed (attempt {new_attempt}/{max_attempts}). Retrying at {next_retry}. Error: {error_message}")
        supabase.table("memory_jobs").update({
            "status": "failed",
            "attempt_count": new_attempt,
            "last_error": error_message,
            "next_retry_at": next_retry,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", job_id).execute()
