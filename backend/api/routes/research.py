from fastapi import APIRouter, HTTPException, BackgroundTasks
from api.schemas.research import (
    ResearchRequest,
    ResearchResponse,
    JobStatusResponse,
    SessionDocumentResponse,
    SessionHistoryResponse,
)
from services import research_service
from services.cache_service import cache
from workers.tasks import run_research_background_task

router = APIRouter()


@router.post("", response_model=ResearchResponse, status_code=202)
def submit_research(body: ResearchRequest, background_tasks: BackgroundTasks):
    """
    POST /research
    Accepts a technical question, creates a session and job in Supabase,
    enqueues the FastAPI background task, and returns immediately.
    """
    # Create session and job records in Supabase
    session = research_service.create_session(body.question)
    job = research_service.create_job(session["id"])

    # Enqueue background task (Runs natively inside the FastAPI process)
    background_tasks.add_task(
        run_research_background_task,
        session_id=session["id"],
        job_id=job["id"],
        question=body.question,
        force_refresh=body.force_refresh,
    )

    return ResearchResponse(
        session_id=session["id"],
        job_id=job["id"],
        status="started",
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str):
    """
    GET /research/jobs/{job_id}
    Returns the current status, progress (0-100), and step of a background job.
    """
    job = research_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    return JobStatusResponse(
        status=job["status"],
        progress=job["progress"],
        step=job["step"],
    )



@router.get("/sessions/{session_id}", response_model=SessionDocumentResponse)
def get_session_document(session_id: str):
    """
    GET /research/sessions/{session_id}
    Returns the completed decision document for the given session, checking cache first.
    """
    cache_key = f"doc_{session_id}"
    cached_doc = cache.get(cache_key)
    if cached_doc:
        return SessionDocumentResponse(document=cached_doc)

    document = research_service.get_document_by_session(session_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    cache.set(cache_key, document)
    return SessionDocumentResponse(document=document)



@router.get("/history", response_model=SessionHistoryResponse)
def get_session_history():
    """
    GET /research/history
    Returns a list of recent completed sessions for the user to select from.
    """
    sessions = research_service.get_recent_sessions(limit=20)
    return SessionHistoryResponse(sessions=sessions)
