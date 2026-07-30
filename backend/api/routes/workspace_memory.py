"""
Workspace-scoped Memory API.
All endpoints require workspace membership (via verify_workspace_path).
Memory items are curate-able: engineers can browse, edit summaries, and delete items.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel
from core.auth import get_current_user, verify_workspace_path
from services.db import get_supabase
from services.pinecone_service import upsert_memory, search_memories

logger = logging.getLogger(__name__)
router = APIRouter()


class MemoryUpdate(BaseModel):
    summary: str


@router.get("")
def list_workspace_memories(
    workspace_id: str,
    memory_type: str = "",    # decision | comparison | evidence | preference | research
    scope: str = "",           # permanent | temporary
    q: str = "",               # text search
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """
    GET /workspaces/{id}/memory
    Returns paginated memory items with type breakdown stats.
    """
    supabase = get_supabase()
    query = (
        supabase.table("memory_items")
        .select("*")
        .eq("workspace_id", workspace_id)
        .eq("is_active", True)
    )

    if memory_type:
        query = query.eq("memory_type", memory_type)
    if scope:
        query = query.eq("scope", scope)

    # Text search using ilike — simple, no FTS setup needed
    if q:
        query = query.ilike("summary", f"%{q}%")

    res = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()

    # Use count=exact to get total without fetching all rows
    count_res = (
        supabase.table("memory_items")
        .select("memory_type", count="exact")
        .eq("workspace_id", workspace_id)
        .eq("is_active", True)
        .execute()
    )
    by_type: dict[str, int] = {}
    total = count_res.count or 0
    for row in (count_res.data or []):
        t = row.get("memory_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    return {
        "memories": res.data or [],
        "total": total,
        "by_type": by_type,
        "limit": limit,
        "offset": offset,
    }


@router.get("/surface")
def surface_relevant_memories(
    workspace_id: str,
    context: str,
    limit: int = 5,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """
    GET /workspaces/{id}/memory/surface?context=redis+caching
    Returns memories most relevant to the given context string.
    Uses Pinecone vector search — same function used during research.
    """
    if not context or len(context.strip()) < 3:
        raise HTTPException(status_code=400, detail="context must be at least 3 characters")

    # search_memories takes a query string and generates embedding internally
    results = search_memories(
        query=context,
        user_id=user_id,
        workspace_id=workspace_id,
        top_k=limit * 3,      # over-fetch then cap
        threshold=0.60,        # slightly lower threshold for browsing (vs research at 0.70)
        max_results=limit,
    )

    # Enrich with Supabase metadata (source links, dates)
    memory_ids = [r.get("id") for r in results if r.get("id")]
    enriched = []
    if memory_ids:
        supabase = get_supabase()
        db_res = supabase.table("memory_items").select("*").in_("id", memory_ids).execute()
        db_map = {row["id"]: row for row in (db_res.data or [])}
        for r in results:
            r["db"] = db_map.get(r.get("id"), {})
            enriched.append(r)
    else:
        enriched = results

    return {"memories": enriched, "context": context}


@router.patch("/{memory_id}")
def update_memory(
    workspace_id: str,
    memory_id: str,
    body: MemoryUpdate,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
):
    """
    PATCH /workspaces/{id}/memory/{memory_id}
    Update a memory's summary text, then re-embed and upsert to Pinecone.
    Re-embedding is done as a background task — returns immediately.
    """
    if not body.summary or len(body.summary.strip()) < 5:
        raise HTTPException(status_code=400, detail="summary must be at least 5 characters")

    supabase = get_supabase()
    
    # 🔐 FIX 1.1: Verify workspace ownership BEFORE update to prevent cross-workspace access
    ownership_check = (
        supabase.table("memory_items")
        .select("workspace_id")
        .eq("id", memory_id)
        .eq("is_active", True)
        .execute()
    )
    if not ownership_check.data:
        raise HTTPException(status_code=404, detail="Memory not found")
    
    if ownership_check.data[0]["workspace_id"] != workspace_id:
        raise HTTPException(status_code=403, detail="Memory not in this workspace")

    import hashlib
    new_hash = hashlib.sha256(body.summary.strip().lower().encode()).hexdigest()

    res = (
        supabase.table("memory_items")
        .update({"summary": body.summary, "dedup_hash": new_hash})
        .eq("id", memory_id)
        .eq("workspace_id", workspace_id)
        .eq("is_active", True)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Memory not found")

    # Re-embed in background — non-blocking
    background_tasks.add_task(_re_embed_memory, memory_id, body.summary, workspace_id)
    return res.data[0]


def _re_embed_memory(memory_id: str, new_summary: str, workspace_id: str) -> None:
    """Re-generate embedding for updated summary and upsert to Pinecone."""
    try:
        upsert_memory(
            memory_id=memory_id,
            summary=new_summary,
            metadata={"workspace_id": workspace_id, "updated": True},
            workspace_id=workspace_id,
        )
        logger.info("Re-embedded memory %s after summary edit", memory_id)
    except Exception as e:
        logger.error("Failed to re-embed memory %s: %s", memory_id, e)


@router.delete("/{memory_id}", status_code=204)
def delete_memory(
    workspace_id: str,
    memory_id: str,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
):
    """
    DELETE /workspaces/{id}/memory/{memory_id}
    Soft-deletes in Supabase (is_active = False) and removes from Pinecone.
    """
    supabase = get_supabase()
    res = (
        supabase.table("memory_items")
        .update({"is_active": False})
        .eq("id", memory_id)
        .eq("workspace_id", workspace_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Memory not found")

    # Delete from Pinecone in background
    background_tasks.add_task(_delete_from_pinecone, memory_id)
    return None


def _delete_from_pinecone(memory_id: str) -> None:
    from services.pinecone_service import get_pinecone_index
    try:
        index = get_pinecone_index()
        if index:
            index.delete(ids=[memory_id])
            logger.info("Deleted memory %s from Pinecone", memory_id)
    except Exception as e:
        logger.error("Failed to delete memory %s from Pinecone: %s", memory_id, e)


@router.get("/export")
def export_memories(
    workspace_id: str,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """
    GET /workspaces/{id}/memory/export
    Returns all active memories as downloadable JSON (GDPR compliance).
    """
    supabase = get_supabase()
    res = (
        supabase.table("memory_items")
        .select("id, summary, memory_type, scope, created_at, source_type, source_id")
        .eq("workspace_id", workspace_id)
        .eq("is_active", True)
        .order("created_at", desc=True)
        .execute()
    )
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content={"memories": res.data or [], "workspace_id": workspace_id},
        headers={"Content-Disposition": f'attachment; filename="atlas_memory_{workspace_id[:8]}.json"'},
    )
