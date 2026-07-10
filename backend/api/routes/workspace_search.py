"""
Workspace-scoped unified search.
Searches across: research_sessions, decision_records, projects, memory_items.
Returns ranked, labeled results.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from core.auth import get_current_user, verify_workspace_path
from services.db import get_supabase

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
def search_workspace(
    workspace_id: str,
    q: str,
    types: str = "research,decisions,projects,memory",   # comma-separated filter
    limit: int = 20,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """
    GET /workspaces/{id}/search?q=redis+caching&types=research,decisions
    Unified search across all workspace artifacts.
    Results are ranked by recency + text match quality.
    """
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="q must be at least 2 characters")

    q = q.strip()
    search_types = {t.strip() for t in types.split(",")}
    supabase = get_supabase()
    results = []

    # Search research sessions
    if "research" in search_types:
        try:
            res = (
                supabase.table("research_sessions")
                .select("id, question, status, created_at")
                .eq("workspace_id", workspace_id)
                .ilike("question", f"%{q}%")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            for row in (res.data or []):
                results.append({
                    "type":       "research",
                    "id":         row["id"],
                    "title":      row["question"],
                    "subtitle":   f"Research · {row.get('status', '')}",
                    "created_at": row["created_at"],
                    "href":       f"/workspaces/{workspace_id}/research?session_id={row['id']}",
                })
        except Exception as e:
            logger.warning("Search error on research_sessions: %s", e)

    # Search decision records (title + join question from research_reports)
    if "decisions" in search_types:
        try:
            res = (
                supabase.table("decision_records")
                .select("id, title, status, created_at, research_session_id")
                .eq("workspace_id", workspace_id)
                .ilike("title", f"%{q}%")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            decisions = res.data or []

            # Also search by research question
            if decisions:
                session_ids = [d["research_session_id"] for d in decisions]
                rep_res = (
                    supabase.table("research_reports")
                    .select("session_id, question")
                    .in_("session_id", session_ids)
                    .execute()
                )
                rep_map = {r["session_id"]: r["question"] for r in (rep_res.data or [])}
            else:
                rep_map = {}

            # Also search decisions whose linked research question matches
            q_res = (
                supabase.table("research_reports")
                .select("session_id, question")
                .ilike("question", f"%{q}%")
                .execute()
            )
            q_session_ids = {r["session_id"] for r in (q_res.data or [])}
            if q_session_ids:
                extra = (
                    supabase.table("decision_records")
                    .select("id, title, status, created_at, research_session_id")
                    .eq("workspace_id", workspace_id)
                    .in_("research_session_id", list(q_session_ids))
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute()
                )
                existing_ids = {d["id"] for d in decisions}
                for row in (extra.data or []):
                    if row["id"] not in existing_ids:
                        decisions.append(row)
                        rep_map[row["research_session_id"]] = next(
                            (r["question"] for r in (q_res.data or []) if r["session_id"] == row["research_session_id"]), ""
                        )

            for row in decisions[:limit]:
                results.append({
                    "type":       "decision",
                    "id":         row["id"],
                    "title":      row["title"],
                    "subtitle":   rep_map.get(row["research_session_id"], ""),
                    "status":     row.get("status"),
                    "created_at": row["created_at"],
                    "href":       f"/workspaces/{workspace_id}/decisions/{row['id']}",
                })
        except Exception as e:
            logger.warning("Search error on decision_records: %s", e)

    # Search projects
    if "projects" in search_types:
        try:
            res = (
                supabase.table("projects")
                .select("id, name, description, status, created_at")
                .eq("workspace_id", workspace_id)
                .or_(f"name.ilike.%{q}%,description.ilike.%{q}%")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            for row in (res.data or []):
                results.append({
                    "type":       "project",
                    "id":         row["id"],
                    "title":      row["name"],
                    "subtitle":   row.get("description", ""),
                    "status":     row.get("status"),
                    "created_at": row["created_at"],
                    "href":       f"/workspaces/{workspace_id}/projects/{row['id']}",
                })
        except Exception as e:
            logger.warning("Search error on projects: %s", e)

    # Search memories
    if "memory" in search_types:
        try:
            res = (
                supabase.table("memory_items")
                .select("id, summary, memory_type, created_at, source_type, source_id")
                .eq("workspace_id", workspace_id)
                .eq("is_active", True)
                .ilike("summary", f"%{q}%")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            for row in (res.data or []):
                results.append({
                    "type":       "memory",
                    "id":         row["id"],
                    "title":      row["summary"][:100],
                    "subtitle":   f"Memory · {row.get('memory_type', '')}",
                    "created_at": row["created_at"],
                    "href":       f"/workspaces/{workspace_id}/memory",
                })
        except Exception as e:
            logger.warning("Search error on memory_items: %s", e)

    # Sort all results by recency
    results.sort(key=lambda r: r.get("created_at", ""), reverse=True)

    return {
        "results": results[:limit],
        "total":   len(results),
        "query":   q,
    }
