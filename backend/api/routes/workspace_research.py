"""
Workspace-scoped research routes.
These replace the flat /research routes for workspace contexts.
The old /research routes remain alive with deprecation headers (see main.py).
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import StreamingResponse
from api.schemas.research import (
    ResearchRequest, ResearchResponse, JobStatusResponse,
    SessionDocumentResponse, SessionHistoryResponse,
)
from services import research_service
from services.cache_service import cache
from services.event_bus import subscribe, unsubscribe
from services.sse_ticket_service import issue_ticket, consume_ticket
from workers.tasks import run_research_background_task
from core.auth import get_current_user, verify_workspace_path
from middleware.rate_limit import limiter
import asyncio
import json
import logging

logger = logging.getLogger(__name__)
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


@router.post("/jobs/{job_id}/stream-ticket")
def get_stream_ticket(
    workspace_id: str,
    job_id: str,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """
    POST /workspaces/{id}/research/jobs/{job_id}/stream-ticket
    Issues a 30-second single-use token to authenticate the SSE connection.
    The frontend calls this with Bearer auth, then uses the ticket on the EventSource URL.
    EventSource does not support custom headers, so Bearer auth cannot be used directly.
    """
    job = research_service.get_job(job_id, user_id=user_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    ticket = issue_ticket(user_id, job_id)
    return {"ticket": ticket, "expires_in": 30}


@router.get("/jobs/{job_id}/stream")
async def stream_job_progress(
    workspace_id: str,
    job_id: str,
    ticket: str,
):
    """
    GET /workspaces/{id}/research/jobs/{job_id}/stream?ticket=...
    Server-Sent Events stream. Auth via single-use ticket (not Bearer header).
    Terminates when: job completes, job fails, client disconnects, or 10-min timeout.
    Nginx/Render buffering is disabled via X-Accel-Buffering: no header.
    """
    identity = consume_ticket(ticket)
    if not identity:
        raise HTTPException(status_code=401, detail="Invalid or expired stream ticket")
    _ticket_user_id, ticket_job_id = identity
    if ticket_job_id != job_id:
        raise HTTPException(status_code=403, detail="Ticket does not match job_id")

    async def event_generator():
        queue = subscribe(job_id)
        MAX_STREAM_SECONDS = 600   # 10-minute hard cap
        loop = asyncio.get_event_loop()
        deadline = loop.time() + MAX_STREAM_SECONDS
        heartbeat_interval = 15

        try:
            # Confirm connection
            yield f"data: {json.dumps({'status': 'connected', 'job_id': job_id})}\n\n"

            # RACE CONDITION FIX: Check if job already finished before we subscribed
            current_job = await asyncio.to_thread(research_service.get_job, job_id, user_id)
            if current_job and current_job.get("status") in ("completed", "failed"):
                # Yield the final state immediately
                final_event = {
                    "status": current_job["status"],
                    "progress": current_job.get("progress", 100),
                    "step": current_job.get("step", ""),
                    "error": "Failed before stream connected" if current_job["status"] == "failed" else None
                }
                yield f"data: {json.dumps(final_event)}\n\n"
                yield "event: done\ndata: {}\n\n"
                return

            while True:
                remaining = deadline - loop.time()
                if remaining <= 0:
                    yield f"data: {json.dumps({'status': 'timeout', 'message': 'Stream max duration reached'})}\n\n"
                    break

                try:
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=min(heartbeat_interval, remaining),
                    )
                    yield f"data: {json.dumps(event)}\n\n"

                    if event.get("status") in ("completed", "failed"):
                        yield "event: done\ndata: {}\n\n"
                        break

                except asyncio.TimeoutError:
                    # Heartbeat — keeps connection alive through proxies
                    yield ": heartbeat\n\n"

        except asyncio.CancelledError:
            logger.debug("SSE client disconnected for job_id=%s", job_id)
        finally:
            unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",   # disable Nginx/Render buffering
            "Connection":        "keep-alive",
        },
    )
