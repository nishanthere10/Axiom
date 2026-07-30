"""
Workspace-scoped Projects API.
Projects are optional containers for organizing research and decisions.
project_id is nullable everywhere — research without a project is fully supported.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from core.auth import get_current_user, verify_workspace_path
from services.db import supabase

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None   # active | completed | archived


class ProjectResponse(BaseModel):
    id: str
    workspace_id: str
    created_by: str
    name: str
    description: Optional[str]
    status: str
    created_at: str
    updated_at: str
    # Aggregated counts — populated in list/detail
    research_count: Optional[int] = 0
    decision_count: Optional[int] = 0


# ── Endpoints ────────────────────────────────────────────────────────────

@router.post("", status_code=201)
def create_project(
    workspace_id: str,
    body: ProjectCreate,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """POST /workspaces/{id}/projects"""
    res = supabase.table("projects").insert({
        "workspace_id": workspace_id,
        "created_by": user_id,
        "name": body.name,
        "description": body.description,
    }).execute()
    return res.data[0]


@router.get("")
def list_projects(
    workspace_id: str,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """
    GET /workspaces/{id}/projects
    Returns all projects for the workspace with research and decision counts.
    """
    projects_res = supabase.table("projects").select("*").eq("workspace_id", workspace_id).order("created_at", desc=True).execute()
    projects = projects_res.data or []

    if not projects:
        return {"projects": []}

    # Fetch counts per project in one query each
    project_ids = [p["id"] for p in projects]

    research_res = supabase.table("research_sessions").select("project_id", count="exact").in_("project_id", project_ids).execute()
    decision_res = supabase.table("decision_records").select("project_id", count="exact").in_("project_id", project_ids).execute()

    # Build count maps
    research_counts: dict[str, int] = {}
    for row in (research_res.data or []):
        pid = row.get("project_id")
        if pid:
            research_counts[pid] = research_counts.get(pid, 0) + 1

    decision_counts: dict[str, int] = {}
    for row in (decision_res.data or []):
        pid = row.get("project_id")
        if pid:
            decision_counts[pid] = decision_counts.get(pid, 0) + 1

    for p in projects:
        p["research_count"] = research_counts.get(p["id"], 0)
        p["decision_count"] = decision_counts.get(p["id"], 0)

    return {"projects": projects}


@router.get("/{project_id}")
def get_project(
    workspace_id: str,
    project_id: str,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """
    GET /workspaces/{id}/projects/{project_id}
    Returns project detail with linked research sessions and decisions.
    """
    logger.info("Fetching project project_id=%s workspace_id=%s user_id=%s", project_id, workspace_id, user_id)
    project_res = supabase.table("projects").select("*").eq("id", project_id).eq("workspace_id", workspace_id).execute()
    if not project_res.data:
        # Diagnostic check: search by project_id alone
        by_id_only = supabase.table("projects").select("*").eq("id", project_id).execute()
        if by_id_only.data:
            actual_ws = by_id_only.data[0].get("workspace_id")
            logger.warning("Project %s exists but workspace_id mismatch! Expected: %s, Found in DB: %s", project_id, workspace_id, actual_ws)
            raise HTTPException(status_code=404, detail=f"Project belongs to workspace {actual_ws}, not current workspace {workspace_id}")
        logger.warning("Project %s not found in database", project_id)
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found in database")
    project = project_res.data[0]

    # Fetch linked research sessions
    research_res = supabase.table("research_sessions").select(
        "id, question, status, created_at"
    ).eq("project_id", project_id).order("created_at", desc=True).execute()

    # Fetch linked decisions (with research report join)
    decisions_res = supabase.table("decision_records").select(
        "id, title, status, created_at, research_session_id"
    ).eq("project_id", project_id).order("created_at", desc=True).execute()

    # Join research questions for decisions
    decisions = decisions_res.data or []
    if decisions:
        session_ids = [d["research_session_id"] for d in decisions]
        reports_res = supabase.table("research_reports").select(
            "session_id, question"
        ).in_("session_id", session_ids).execute()
        reports_map = {r["session_id"]: r for r in (reports_res.data or [])}
        for d in decisions:
            d["question"] = reports_map.get(d["research_session_id"], {}).get("question")

    project["research_count"] = len(research_res.data or [])
    project["decision_count"] = len(decisions)

    return {
        "project": project,
        "research": research_res.data or [],
        "decisions": decisions,
    }


@router.patch("/{project_id}")
def update_project(
    workspace_id: str,
    project_id: str,
    body: ProjectUpdate,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """PATCH /workspaces/{id}/projects/{project_id}"""
    payload = body.dict(exclude_unset=True)
    if not payload:
        raise HTTPException(status_code=400, detail="No fields to update")

    res = supabase.table("projects").update(payload).eq("id", project_id).eq("workspace_id", workspace_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    return res.data[0]


@router.delete("/{project_id}", status_code=204)
def delete_project(
    workspace_id: str,
    project_id: str,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """
    DELETE /workspaces/{id}/projects/{project_id}
    Soft delete: sets status = 'archived'.
    Linked research_sessions and decision_records have project_id SET NULL (via FK ON DELETE SET NULL).
    """
    res = supabase.table("projects").update({"status": "archived"}).eq("id", project_id).eq("workspace_id", workspace_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Project not found or unauthorized")
    return None


@router.post("/{project_id}/research/{session_id}")
def assign_research_to_project(
    workspace_id: str,
    project_id: str,
    session_id: str,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """POST /workspaces/{id}/projects/{project_id}/research/{session_id} — Assign an existing session to a project."""
    res = supabase.table("research_sessions").update({"project_id": project_id}).eq("id", session_id).eq("workspace_id", workspace_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Research session not found or unauthorized")
    return {"success": True}


@router.post("/{project_id}/decisions/{decision_id}")
def assign_decision_to_project(
    workspace_id: str,
    project_id: str,
    decision_id: str,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """POST /workspaces/{id}/projects/{project_id}/decisions/{decision_id} — Assign an existing decision to a project."""
    res = supabase.table("decision_records").update({"project_id": project_id}).eq("id", decision_id).eq("workspace_id", workspace_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Decision not found or unauthorized")
    return {"success": True}
