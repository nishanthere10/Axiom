from services.db import supabase


def create_session(question: str, user_id: str = "anonymous", workspace_id: str | None = None) -> dict:
    """Create a research session row. Returns the created row."""
    payload = {"question": question, "status": "draft", "version": 1, "user_id": user_id}
    if workspace_id:
        payload["workspace_id"] = workspace_id
    response = (
        supabase.table("research_sessions")
        .insert(payload)
        .execute()
    )
    return response.data[0]


def create_job(session_id: str) -> dict:
    """Create a research job row. Returns the created row."""
    response = (
        supabase.table("research_jobs")
        .insert({"session_id": session_id, "status": "queued", "progress": 0, "step": ""})
        .execute()
    )
    return response.data[0]


def update_job_status(job_id: str, status: str, progress: int = 0, step: str = "") -> None:
    """Update job status, progress, and current step."""
    supabase.table("research_jobs").update(
        {"status": status, "progress": progress, "step": step}
    ).eq("id", job_id).execute()


def update_session_status(session_id: str, status: str) -> None:
    """Update session status."""
    supabase.table("research_sessions").update({"status": status}).eq("id", session_id).execute()


def save_document(session_id: str, question: str, state: dict, user_id: str = "anonymous", warnings: list = None) -> dict:
    """Save the final decision document to Supabase."""
    from datetime import datetime
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
        "evidence_generated_at": datetime.utcnow().isoformat() if evidence else None,
        "evidence_generated_at": datetime.utcnow().isoformat() if evidence else None,
        "version": 1,
        "user_id": user_id,
    }
    # Retrieve the workspace_id from the session and add to document
    session = supabase.table("research_sessions").select("workspace_id").eq("id", session_id).execute()
    if session.data and session.data[0].get("workspace_id"):
        payload["workspace_id"] = session.data[0]["workspace_id"]
        
    response = supabase.table("research_reports").insert(payload).execute()
    return response.data[0]


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


def get_recent_sessions(limit: int = 10, offset: int = 0, user_id: str = "anonymous", workspace_id: str | None = None) -> list[dict]:
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
