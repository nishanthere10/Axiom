"""Workspace-scoped decision routes."""
import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from api.schemas.decision import DecisionRecordCreate, DecisionRecordUpdate, DecisionRecordResponse, DecisionListResponse
from core.auth import get_current_user, verify_workspace_path
from services.db import supabase
from services.decision_memory_service import generate_and_store_decision_memory

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=DecisionRecordResponse, status_code=201)
def create_decision_in_workspace(
    workspace_id: str,
    body: DecisionRecordCreate,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """POST /workspaces/{id}/decisions"""
    existing = supabase.table("decision_records").select("id").eq("research_session_id", body.research_session_id).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="A decision record already exists for this session.")

    res = supabase.table("decision_records").insert({
        "workspace_id": workspace_id,
        "research_session_id": body.research_session_id,
        "title": body.title,
        "status": body.status,
        "created_by": user_id,
    }).execute()
    return _get_decision_with_report(res.data[0]["id"])


@router.get("", response_model=DecisionListResponse)
def list_decisions_in_workspace(
    workspace_id: str,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """GET /workspaces/{id}/decisions"""
    res = supabase.table("decision_records").select("*").eq("workspace_id", workspace_id).order("created_at", desc=True).execute()
    decisions = res.data or []
    if not decisions:
        return DecisionListResponse(decisions=[])

    session_ids = [d["research_session_id"] for d in decisions]
    reports_res = supabase.table("research_reports").select(
        "session_id, question, recommendation_context, executive_summary, alternatives"
    ).in_("session_id", session_ids).execute()
    reports_map = {r["session_id"]: r for r in reports_res.data}

    for d in decisions:
        report = reports_map.get(d["research_session_id"], {})
        d.update({"question": report.get("question"), "recommendation_context": report.get("recommendation_context"),
                   "executive_summary": report.get("executive_summary"), "alternatives": report.get("alternatives")})

    return DecisionListResponse(decisions=decisions)


@router.get("/search")
def search_decisions(
    workspace_id: str,
    q: str = "",
    status: str = "",
    limit: int = 20,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """
    GET /workspaces/{id}/decisions/search?q=redis&status=APPROVED&limit=20
    Full-text search over decision titles and linked research questions.
    Uses Supabase PostgREST ilike for simple substring matching.
    """
    query = supabase.table("decision_records").select(
        "id, title, status, created_at, research_session_id, created_by"
    ).eq("workspace_id", workspace_id)

    if status:
        query = query.eq("status", status.upper())

    results = query.order("created_at", desc=True).limit(limit * 3).execute()
    decisions = results.data or []

    if not decisions:
        return {"results": [], "total": 0}

    # Fetch linked research questions for text matching
    session_ids = [d["research_session_id"] for d in decisions]
    reports_res = supabase.table("research_reports").select(
        "session_id, question, executive_summary"
    ).in_("session_id", session_ids).execute()
    reports_map = {r["session_id"]: r for r in (reports_res.data or [])}

    # Filter in Python — search across title + question
    if q:
        q_lower = q.lower()
        filtered = []
        for d in decisions:
            report = reports_map.get(d["research_session_id"], {})
            title_match = q_lower in (d.get("title") or "").lower()
            question_match = q_lower in (report.get("question") or "").lower()
            summary_match = q_lower in (report.get("executive_summary") or "").lower()
            if title_match or question_match or summary_match:
                d["question"] = report.get("question")
                d["executive_summary"] = report.get("executive_summary")
                filtered.append(d)
        decisions = filtered
    else:
        for d in decisions:
            report = reports_map.get(d["research_session_id"], {})
            d["question"] = report.get("question")
            d["executive_summary"] = report.get("executive_summary")

    decisions = decisions[:limit]
    return {"results": decisions, "total": len(decisions)}


@router.get("/{decision_id}/full")
def get_decision_full(
    workspace_id: str,
    decision_id: str,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """
    GET /workspaces/{id}/decisions/{decision_id}/full
    Returns the complete decision with:
    - Decision record
    - Linked research report (question, summary, confidence, evidence, alternatives)
    - Status change history
    """
    # Decision record
    res = supabase.table("decision_records").select("*").eq("id", decision_id).eq("workspace_id", workspace_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Decision not found")
    decision = res.data[0]

    # Linked research report
    report_res = supabase.table("research_reports").select(
        "question, executive_summary, recommendation_context, alternatives, confidence, tradeoffs, evidence"
    ).eq("session_id", decision["research_session_id"]).execute()
    report = report_res.data[0] if report_res.data else {}

    # Status history
    history_res = supabase.table("decision_status_history").select("*").eq("decision_id", decision_id).order("changed_at", desc=False).execute()
    history = history_res.data or []

    return {
        "decision": decision,
        "research": report,
        "history": history,
    }


@router.patch("/{decision_id}", response_model=DecisionRecordResponse)
def update_decision_in_workspace(
    workspace_id: str,
    decision_id: str,
    body: DecisionRecordUpdate,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path),
):
    """PATCH /workspaces/{id}/decisions/{decision_id}"""
    # Fetch current status for history
    current = supabase.table("decision_records").select("status").eq("id", decision_id).execute()
    if not current.data:
        raise HTTPException(status_code=404, detail="Decision not found")
    from_status = current.data[0]["status"]

    # Build update payload
    payload = {"status": body.status}
    if body.title:
        payload["title"] = body.title

    # Write history row BEFORE updating
    try:
        supabase.table("decision_status_history").insert({
            "decision_id": decision_id,
            "from_status": from_status,
            "to_status": body.status,
            "changed_by": user_id,
            "note": getattr(body, "note", None),  # optional note field
        }).execute()
    except Exception as e:
        logger.warning("Failed to write decision history row: %s", e)
        # Non-fatal — proceed with the update

    # Update the decision
    res = supabase.table("decision_records").update(payload).eq("id", decision_id).eq("created_by", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Decision not found or unauthorized")

    if body.status in ["APPROVED", "IMPLEMENTED"]:
        background_tasks.add_task(generate_and_store_decision_memory, decision_id, user_id)

    return _get_decision_with_report(decision_id)


def _get_decision_with_report(decision_id: str) -> dict:
    res = supabase.table("decision_records").select("*").eq("id", decision_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Decision not found")
    row = res.data[0]
    reports_res = supabase.table("research_reports").select(
        "question, recommendation_context, executive_summary, alternatives"
    ).eq("session_id", row["research_session_id"]).execute()
    report = reports_res.data[0] if reports_res.data else {}
    row.update(report)
    return row
