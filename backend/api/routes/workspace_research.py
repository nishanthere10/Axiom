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
    RegenerateVisualsRequest, RegenerateVisualsResponse,
)
from services import research_service
from services.cache_service import cache
from services.event_bus import subscribe, unsubscribe
from services.sse_ticket_service import issue_ticket, consume_ticket, peek_ticket
from workers.tasks import run_research_background_task
from core.auth import get_current_user, verify_workspace_path, verify_workspace_owner_path
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
    _ws: str = Depends(verify_workspace_owner_path),
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
    job = research_service.get_job(job_id, user_id=user_id, workspace_id=workspace_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobStatusResponse(status=job["status"], progress=job["progress"], step=job["step"])


@router.get("/sessions/{session_id}", response_model=SessionDocumentResponse)
def get_session_document(workspace_id: str, session_id: str, user_id: str = Depends(get_current_user), _ws: str = Depends(verify_workspace_path)):
    """GET /workspaces/{id}/research/sessions/{session_id}"""
    cache_key = f"doc_ws_{workspace_id}_{session_id}"
    cached_doc = cache.get(cache_key)
    # Only serve from cache if the document has visuals — a cache miss on visuals
    # means the document was cached before the visual spec node finished writing.
    if cached_doc and cached_doc.get("visuals"):
        return SessionDocumentResponse(document=cached_doc)
    elif cached_doc:
        # Stale cache entry (no visuals) — bust it and re-fetch from DB
        cache.delete(cache_key)

    document = research_service.get_document_by_session(session_id, user_id=user_id, workspace_id=workspace_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Only cache once visuals are present to avoid poisoning subsequent reads
    if document.get("visuals"):
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


@router.post("/regenerate-visuals", response_model=RegenerateVisualsResponse)
async def regenerate_visuals_in_workspace(
    workspace_id: str,
    body: RegenerateVisualsRequest,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_owner_path),
):
    """POST /workspaces/{id}/research/regenerate-visuals
    Regenerates only the visuals for an existing session and updates the database.
    """
    import anyio
    from agents.nodes.generate_visual_spec import generate_visual_spec
    from agents.nodes.validate_visual_spec import validate_visual_spec
    from services.db import get_supabase
    from datetime import datetime

    document = await anyio.to_thread.run_sync(
        research_service.get_document_by_session, body.session_id, user_id, workspace_id
    )
    if not document:
        raise HTTPException(status_code=404, detail="Session document not found.")

    # Reconstruct minimal state needed by the visual spec node
    initial_state = {
        "question":       document.get("question", ""),
        "summary":        document.get("executive_summary", ""),
        "recommendation": document.get("recommendation_context", ""),
        "tradeoffs":      document.get("tradeoffs", ""),
        "alternatives":   document.get("alternatives", ""),
        "confidence":     document.get("confidence", {}),
        "evidence":       document.get("evidence", []),
        "visual_specs":   [],
        "visuals":        [],
    }

    state_after_gen = await generate_visual_spec(initial_state)
    initial_state.update(state_after_gen)

    # validate_visual_spec is synchronous
    state_after_val = await anyio.to_thread.run_sync(validate_visual_spec, initial_state)
    visuals = state_after_val.get("visuals", [])

    # Persist updated visuals and bust the document cache
    supabase = get_supabase()
    await anyio.to_thread.run_sync(
        lambda: supabase.table("research_reports").update({
            "visuals": visuals,
            "visuals_updated_at": datetime.utcnow().isoformat(),
        }).eq("session_id", body.session_id).execute()
    )
    cache.delete(f"doc_ws_{workspace_id}_{body.session_id}")
    cache.delete(f"doc_{user_id}_{body.session_id}")  # Also clean up any legacy user-scoped cache

    logger.info("Regenerated %d visuals for session %s", len(visuals), body.session_id)
    return RegenerateVisualsResponse(visuals=visuals)


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
    job = research_service.get_job(job_id, user_id=user_id, workspace_id=workspace_id)
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
    # 🔐 FIX 1.2: Verify ticket WITHOUT consuming it first
    # This prevents ticket burn if job verification fails
    identity = peek_ticket(ticket)
    if not identity:
        raise HTTPException(status_code=401, detail="Invalid or expired stream ticket")
    
    _ticket_user_id, ticket_job_id = identity
    if ticket_job_id != job_id:
        raise HTTPException(status_code=403, detail="Ticket does not match job_id")
    
    # Verify job exists and user has access BEFORE consuming ticket
    job_check = await asyncio.to_thread(research_service.get_job, job_id, _ticket_user_id, workspace_id)
    if not job_check:
        raise HTTPException(status_code=404, detail="Job not found or access denied")
    
    # NOW it's safe to consume the ticket
    consume_ticket(ticket)

    async def event_generator():
        # 🔐 FIX 2.1: Subscribe FIRST, then check job status atomically
        # This prevents race where job completes between subscription and check
        queue = subscribe(job_id)
        MAX_STREAM_SECONDS = 600   # 10-minute hard cap
        loop = asyncio.get_running_loop()
        deadline = loop.time() + MAX_STREAM_SECONDS
        heartbeat_interval = 15

        try:
            # Confirm connection
            yield f"data: {json.dumps({'status': 'connected', 'job_id': job_id})}\n\n"

            # CRITICAL: Check job status AFTER subscribe to catch any completion events
            # that happened between our check above and now
            current_job = await asyncio.to_thread(research_service.get_job, job_id, _ticket_user_id, workspace_id)
            if current_job and current_job.get("status") in ("completed", "failed"):
                # Yield the final state immediately
                final_event = {
                    "status": current_job["status"],
                    "progress": current_job.get("progress", 100),
                    "step": current_job.get("step", ""),
                    "error": current_job.get("step") if current_job["status"] == "failed" else None
                }
                yield f"data: {json.dumps(final_event)}\n\n"
                yield "event: done\ndata: {}\n\n"
                unsubscribe(job_id, queue)  # Clean up immediately
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
