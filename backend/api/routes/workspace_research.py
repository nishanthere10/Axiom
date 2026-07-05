"""
Workspace-scoped research routes.
These replace the flat /research routes for workspace contexts.
The old /research routes remain alive with deprecation headers (see main.py).
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from api.schemas.research import (
    ResearchRequest, ResearchResponse, JobStatusResponse,
    SessionDocumentResponse, SessionHistoryResponse,
)
from services import research_service
from services.cache_service import cache
from workers.tasks import run_research_background_task
from core.auth import get_current_user, verify_workspace_path
from middleware.rate_limit import limiter

router = APIRouter()


@router.post("", response_model=ResearchResponse, status_code=202)
@limiter.limit("5/minute")
def submit_research_in_workspace(
    request: Request,
    workspace_id: str,
    body: ResearchRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """POST /workspaces/{id}/research"""
    # Create the research session, scoped to the workspace and project (if any)
    session = research_service.create_session(
        body.question,
        user_id=user_id,
        workspace_id=workspace_id,
        project_id=body.project_id
    )
    job = research_service.create_job(session["id"])

    background_tasks.add_task(
        run_research_background_task,
        session_id=session["id"],
        job_id=job["id"],
        question=body.question,
        force_refresh=body.force_refresh,
        user_id=user_id,
        workspace_id=workspace_id,
    )
    return ResearchResponse(session_id=session["id"], job_id=job["id"], status="started")


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job_status(workspace_id: str, job_id: str, user_id: str = Depends(get_current_user), _ws: str = Depends(verify_workspace_path)):
    """GET /workspaces/{id}/research/jobs/{job_id}"""
    job = research_service.get_job(job_id, user_id=user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatusResponse(status=job["status"], progress=job["progress"], step=job["step"])


@router.get("/sessions/{session_id}", response_model=SessionDocumentResponse)
def get_session_document(workspace_id: str, session_id: str, user_id: str = Depends(get_current_user), _ws: str = Depends(verify_workspace_path)):
    """GET /workspaces/{id}/research/sessions/{session_id}"""
    cache_key = f"doc_{user_id}_{session_id}"
    cached_doc = cache.get(cache_key)
    if cached_doc:
        return SessionDocumentResponse(document=cached_doc)

    document = research_service.get_document_by_session(session_id, user_id=user_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    cache.set(cache_key, document)
    return SessionDocumentResponse(document=document)


@router.get("/history", response_model=SessionHistoryResponse)
def get_research_history(
    workspace_id: str,
    limit: int = 10,
    offset: int = 0,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """GET /workspaces/{id}/research/history"""
    sessions = research_service.get_recent_sessions(
        limit=limit, offset=offset, user_id=user_id, workspace_id=workspace_id
    )
    return SessionHistoryResponse(sessions=sessions)
