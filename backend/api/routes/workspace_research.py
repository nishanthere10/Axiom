"""
Workspace-scoped research routes.
These replace the flat /research routes for workspace contexts.
The old /research routes remain alive with deprecation headers (see main.py).
"""
from typing import Dict, Any
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


def _sanitize_sse_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    SECURITY FIX: Sanitize SSE event data to prevent information disclosure.
    Removes sensitive internal details while preserving user-relevant information.
    """
    sanitized = {
        "status": event.get("status", "unknown"),
        "progress": event.get("progress", 0),
        "step": event.get("step", ""),
        "node": event.get("node", ""),
    }
    
    # Only include safe metadata
    meta = event.get("meta", {})
    if isinstance(meta, dict):
        safe_meta = {}
        # Allow specific safe fields
        for key in ["memories_found", "github_chunks"]:
            if key in meta and isinstance(meta[key], (int, str)):
                safe_meta[key] = meta[key]
        
        # Sanitize memory summaries
        if "memory_summaries" in meta and isinstance(meta["memory_summaries"], list):
            safe_meta["memory_summaries"] = [
                str(summary)[:50] + "..." if len(str(summary)) > 50 else str(summary)
                for summary in meta["memory_summaries"][:3]  # Limit to 3 items
            ]
        
        if safe_meta:
            sanitized["meta"] = safe_meta
    
    # Sanitize error messages
    if event.get("status") == "failed":
        error = event.get("error", "")
        if error:
            # Replace internal error details with generic message
            sanitized["error"] = "Processing failed. Please try again."
        
    return sanitized


async def verify_workspace_access_by_user_id(user_id: str, workspace_id: str) -> bool:
    """
    SECURITY FIX: Additional workspace verification helper for SSE authentication.
    Provides defense-in-depth by double-checking workspace access.
    """
    try:
        from services.db import get_supabase
        supabase = get_supabase("api")  # SECURITY FIX: Use API context
        
        response = supabase.table("workspace_members")\
            .select("id")\
            .eq("workspace_id", workspace_id)\
            .eq("user_id", user_id)\
            .limit(1)\
            .execute()
            
        return bool(response.data)
    except Exception as e:
        logger.error(f"Workspace verification failed: {e}")
        return False


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
    
    SECURITY FIX: Proper ticket validation order to prevent race conditions.
    """
    # SECURITY FIX: Complete validation BEFORE consuming ticket
    
    # Step 1: Peek ticket without consuming
    identity = peek_ticket(ticket)
    if not identity:
        raise HTTPException(status_code=401, detail="Invalid or expired stream ticket")
    
    _ticket_user_id, ticket_job_id = identity
    if ticket_job_id != job_id:
        raise HTTPException(status_code=403, detail="Ticket does not match job_id")
    
    # Step 2: Verify job exists and user has complete access
    try:
        job_check = await asyncio.to_thread(
            research_service.get_job, 
            job_id, 
            _ticket_user_id, 
            workspace_id
        )
        if not job_check:
            raise HTTPException(status_code=404, detail="Job not found or access denied")
    except Exception as e:
        logger.warning(f"Job verification failed for job_id={job_id}, user={_ticket_user_id}: {e}")
        raise HTTPException(status_code=500, detail="Job verification failed")
    
    # Step 3: Verify workspace access separately for defense-in-depth
    try:
        from core.auth import verify_workspace_access_by_user_id
        workspace_check = await verify_workspace_access_by_user_id(_ticket_user_id, workspace_id)
        if not workspace_check:
            raise HTTPException(status_code=403, detail="Workspace access denied")
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Workspace verification failed for user={_ticket_user_id}, workspace={workspace_id}: {e}")
        raise HTTPException(status_code=500, detail="Workspace verification failed")
    
    # Step 4: NOW safe to consume ticket after all validations pass
    try:
        consume_ticket(ticket)
    except Exception as e:
        logger.error(f"Failed to consume ticket: {e}")
        raise HTTPException(status_code=500, detail="Ticket consumption failed")

    async def event_generator():
        queue = None
        try:
            # SECURITY FIX: Subscribe with timeout protection
            queue = subscribe(job_id)
            MAX_STREAM_SECONDS = 600   # 10-minute hard cap
            loop = asyncio.get_running_loop()
            deadline = loop.time() + MAX_STREAM_SECONDS
            heartbeat_interval = 15

            # Confirm connection with sanitized data
            yield f"data: {json.dumps({'status': 'connected', 'job_id': job_id})}\n\n"

            # Check job status immediately after subscription
            current_job = await asyncio.to_thread(
                research_service.get_job, 
                job_id, 
                _ticket_user_id, 
                workspace_id
            )
            
            if current_job:
                # Always send the current state so late-connecting clients get immediate progress
                error_msg = None
                if current_job.get("status") == "failed":
                    error_msg = "Processing failed"
                    
                initial_event = {
                    "status": current_job.get("status", "running"),
                    "progress": current_job.get("progress", 0),
                    "step": current_job.get("step", ""),
                    "error": error_msg
                }
                yield f"data: {json.dumps(initial_event)}\n\n"
                
                if current_job.get("status") in ("completed", "failed"):
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
                    
                    # SECURITY FIX: Sanitize event data before sending
                    sanitized_event = _sanitize_sse_event(event)
                    yield f"data: {json.dumps(sanitized_event)}\n\n"

                    if event.get("status") in ("completed", "failed"):
                        yield "event: done\ndata: {}\n\n"
                        break

                except asyncio.TimeoutError:
                    # Heartbeat — keeps connection alive through proxies
                    yield ": heartbeat\n\n"

        except asyncio.CancelledError:
            logger.debug("SSE client disconnected for job_id=%s", job_id)
        except Exception as e:
            logger.error(f"SSE stream error for job {job_id}: {e}")
            yield f"data: {json.dumps({'status': 'error', 'message': 'Stream error occurred'})}\n\n"
        finally:
            if queue:
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
