from services.db import supabase


def create_session(question: str) -> dict:
    """Create a research session row. Returns the created row."""
    response = (
        supabase.table("research_sessions")
        .insert({"question": question, "status": "draft", "version": 1})
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


def save_document(session_id: str, question: str, state: dict) -> dict:
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
        "evidence_generated_at": datetime.utcnow().isoformat() if evidence else None,
        "version": 1,
    }
    response = supabase.table("decision_documents").insert(payload).execute()
    return response.data[0]


def get_job(job_id: str) -> dict | None:
    """Fetch a job row by ID."""
    response = supabase.table("research_jobs").select("*").eq("id", job_id).execute()
    if response.data:
        return response.data[0]
    return None


def get_document_by_session(session_id: str) -> dict | None:
    """Fetch the decision document for a given session ID."""
    response = (
        supabase.table("decision_documents")
        .select("*")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if response.data:
        return response.data[0]
    return None


def get_recent_sessions(limit: int = 10, offset: int = 0) -> list[dict]:
    """Fetch recent completed research sessions with pagination."""
    response = (
        supabase.table("research_sessions")
        .select("id, question, created_at")
        .eq("status", "complete")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return response.data or []
