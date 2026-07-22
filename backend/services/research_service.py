from services.db import supabase
import logging
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Shared retry policy for ALL Supabase/PostgREST network calls
_SUPABASE_RETRY = dict(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError)),
    reraise=True,
)


@retry(**_SUPABASE_RETRY)
def create_session(question: str, user_id: str, workspace_id: str | None = None, project_id: str | None = None) -> dict:
    """Create a research session row. Returns the created row."""
    payload = {"question": question, "status": "draft", "version": 1, "user_id": user_id}
    if workspace_id:
        payload["workspace_id"] = workspace_id
    if project_id:
        payload["project_id"] = project_id
    response = (
        supabase.table("research_sessions")
        .insert(payload)
        .execute()
    )
    return response.data[0]


@retry(**_SUPABASE_RETRY)
def create_job(session_id: str) -> dict:
    """Create a research job row. Returns the created row."""
    response = (
        supabase.table("research_jobs")
        .insert({"session_id": session_id, "status": "queued", "progress": 0, "step": ""})
        .execute()
    )
    return response.data[0]


@retry(**_SUPABASE_RETRY)
def update_job_status(job_id: str, status: str, progress: int = 0, step: str = "") -> None:
    """Update job status, progress, and current step."""
    supabase.table("research_jobs").update(
        {"status": status, "progress": progress, "step": step}
    ).eq("id", job_id).execute()


@retry(**_SUPABASE_RETRY)
def update_session_status(session_id: str, status: str) -> None:
    """Update session status."""
    supabase.table("research_sessions").update({"status": status}).eq("id", session_id).execute()


@retry(**_SUPABASE_RETRY)
def save_document(session_id: str, question: str, state: dict, user_id: str, warnings: list = None) -> dict:
    """Save the final decision document to Supabase."""
    from datetime import datetime, timezone
    confidence = state.get("confidence", {})
    evidence = state.get("evidence", [])
    visuals = state.get("visuals", [])

    payload = {
        "session_id": session_id,
        "question": question,
        "executive_summary": state.get("summary", ""),
        "recommendation_context": state.get("recommendation", ""),
        "tradeoffs": state.get("tradeoffs", ""),
        "alternatives": state.get("alternatives", ""),
        "confidence": confidence,
        "evidence": evidence,
        "consensus": state.get("consensus", ""),
        "visuals": visuals,
        "memory_context": state.get("memory_context", {}),
        "warnings": warnings or [],
        "evidence_generated_at": datetime.now(timezone.utc).isoformat() if evidence else None,
        "version": 1,
        "user_id": user_id,
    }
    # Retrieve the workspace_id and project_id from the session to stamp the document and decision record
    session = supabase.table("research_sessions").select("workspace_id, project_id").eq("id", session_id).execute()
    workspace_id = None
    project_id = None
    if session.data:
        workspace_id = session.data[0].get("workspace_id")
        project_id = session.data[0].get("project_id")

    if workspace_id:
        payload["workspace_id"] = workspace_id

    response = supabase.table("research_reports").insert(payload).execute()

    # Immediately bust the in-memory document cache so the next GET always reads
    # the freshly-written row (with visuals) rather than an empty-visuals entry
    # that may have been cached before the pipeline finished.
    try:
        from services.cache_service import cache as _cache
        _cache.delete(f"doc_{user_id}_{session_id}")
    except Exception:
        pass
    
    # Auto-create the decision record
    if workspace_id:
        try:
            decision_title = question[:80] + ("..." if len(question) > 80 else "")
            supabase.table("decision_records").insert({
                "workspace_id": workspace_id,
                "project_id": project_id,
                "research_session_id": session_id,
                "title": decision_title,
                "status": "PROPOSED",
                "created_by": user_id,
            }).execute()
        except Exception as e:
            # We don't want to fail the whole background task if this fails, but it shouldn't
            logger.warning("Failed to auto-create decision_record for session %s: %s", session_id, e)

    return response.data[0]


@retry(**_SUPABASE_RETRY)
def get_job(job_id: str, user_id: str) -> dict | None:
    """Fetch a job row by ID, joined with session to verify ownership."""
    response = (
        supabase.table("research_jobs")
        .select("*, research_sessions!inner(user_id)")
        .eq("id", job_id)
        .eq("research_sessions.user_id", user_id)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


@retry(**_SUPABASE_RETRY)
def get_document_by_session(session_id: str, user_id: str) -> dict | None:
    """Fetch the decision document for a given session ID, scoped to user."""
    response = (
        supabase.table("research_reports")
        .select("*")
        .eq("session_id", session_id)
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


@retry(**_SUPABASE_RETRY)
def get_recent_sessions(user_id: str, limit: int = 10, offset: int = 0, workspace_id: str | None = None) -> list[dict]:
    """Fetch recent completed research sessions for a specific user and workspace with pagination."""
    query = (
        supabase.table("research_sessions")
        .select("id, question, created_at")
        .eq("status", "complete")
        .eq("user_id", user_id)
    )
    if workspace_id:
        query = query.eq("workspace_id", workspace_id)

    response = (
        query.order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return response.data or []


@retry(**_SUPABASE_RETRY)
def recover_stale_jobs() -> None:
    """Find running jobs older than 15 mins and mark failed."""
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    try:
        supabase.table("research_jobs").update(
            {"status": "failed", "step": "timeout"}
        ).eq("status", "running").lt("created_at", cutoff).execute()
    except Exception as e:
        pass
