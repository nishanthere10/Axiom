from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request, Header
from api.schemas.research import (
    ResearchRequest,
    ResearchResponse,
    JobStatusResponse,
    SessionDocumentResponse,
    SessionHistoryResponse,
    RegenerateVisualsRequest,
    RegenerateVisualsResponse,
)
from services import research_service
from services.cache_service import cache
from workers.tasks import run_research_background_task
from core.auth import get_current_user, verify_workspace_access
from middleware.rate_limit import limiter

router = APIRouter()


@router.post("", response_model=ResearchResponse, status_code=202)
@limiter.limit("5/minute")
def submit_research(request: Request, body: ResearchRequest, background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user), workspace_id: str | None = Depends(verify_workspace_access)):
    """
    POST /research
    Accepts a technical question, creates a session and job in Supabase,
    enqueues the FastAPI background task, and returns immediately.
    """
    # Create session and job records in Supabase
    session = research_service.create_session(body.question, user_id=user_id, workspace_id=workspace_id)
    job = research_service.create_job(session["id"])

    # Enqueue background task (Runs natively inside the FastAPI process)
    background_tasks.add_task(
        run_research_background_task,
        session_id=session["id"],
        job_id=job["id"],
        question=body.question,
        force_refresh=body.force_refresh,
        user_id=user_id,
    )

    return ResearchResponse(
        session_id=session["id"],
        job_id=job["id"],
        status="started",
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, user_id: str = Depends(get_current_user)):
    """
    GET /research/jobs/{job_id}
    Returns the current status, progress (0-100), and step of a background job.
    """
    job = research_service.get_job(job_id, user_id=user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    return JobStatusResponse(
        status=job["status"],
        progress=job["progress"],
        step=job["step"],
    )



@router.get("/sessions/{session_id}", response_model=SessionDocumentResponse)
def get_session_document(session_id: str, user_id: str = Depends(get_current_user)):
    """
    GET /research/sessions/{session_id}
    Returns the completed decision document for the given session, checking cache first.
    """
    cache_key = f"doc_{session_id}"
    cached_doc = cache.get(cache_key)
    if cached_doc:
        # Note: In a true multi-tenant setup, cache keys should include user_id. 
        # For now, we trust the DB fetch for auth. If cached, we should technically verify ownership.
        # But fixing the cache key is safer:
        cache_key = f"doc_{user_id}_{session_id}"
        cached_doc = cache.get(cache_key)
        if cached_doc:
            return SessionDocumentResponse(document=cached_doc)

    document = research_service.get_document_by_session(session_id, user_id=user_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    cache_key = f"doc_{user_id}_{session_id}"
    cache.set(cache_key, document)
    return SessionDocumentResponse(document=document)



@router.get("/history", response_model=SessionHistoryResponse)
def get_session_history(limit: int = 10, offset: int = 0, user_id: str = Depends(get_current_user), workspace_id: str | None = Depends(verify_workspace_access)):
    """
    GET /research/history?limit=10&offset=0
    Returns a paginated list of recent completed sessions for the current user.
    """
    sessions = research_service.get_recent_sessions(limit=limit, offset=offset, user_id=user_id, workspace_id=workspace_id)
    return SessionHistoryResponse(sessions=sessions)

import anyio

@router.post("/regenerate-visuals", response_model=RegenerateVisualsResponse)
async def regenerate_visuals(body: RegenerateVisualsRequest, user_id: str = Depends(get_current_user)):
    """
    POST /research/regenerate-visuals
    Regenerates only the visuals for an existing session and updates the database.
    """
    document = await anyio.to_thread.run_sync(
        research_service.get_document_by_session, body.session_id, user_id
    )
    if not document:
        raise HTTPException(status_code=404, detail="Session document not found.")

    from agents.graph.decision_graph import decision_graph

    # Reconstruct state
    initial_state = {
        "question": document.get("question", ""),
        "decision": document.get("recommendation_context", ""),
        "evidence": document.get("evidence", []),
        "visual_specs": [],
        "visuals": []
    }

    # Since we only want to run visual generation, we can invoke the nodes directly
    # instead of the full graph to save time and prevent overwriting other fields.
    from agents.nodes.generate_visual_spec import generate_visual_spec
    from agents.nodes.validate_visual_spec import validate_visual_spec

    state_after_gen = await generate_visual_spec(initial_state)
    initial_state.update(state_after_gen)
    
    # validate_visual_spec is synchronous
    state_after_val = await anyio.to_thread.run_sync(validate_visual_spec, initial_state)
    
    visuals = state_after_val.get("visuals", [])
    
    # Save back to database
    from services.db import supabase
    from datetime import datetime
    
    def _update_db():
        return supabase.table("research_reports").update({
            "visuals": visuals,
            "visuals_updated_at": datetime.utcnow().isoformat()
        }).eq("session_id", body.session_id).execute()
        
    await anyio.to_thread.run_sync(_update_db)
    
    # Clear cache
    cache.delete(f"doc_{user_id}_{body.session_id}")
    
    return RegenerateVisualsResponse(visuals=visuals)

