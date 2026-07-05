import logging
from fastapi import APIRouter, HTTPException, Depends, Header, BackgroundTasks, Response
from api.schemas.decision import DecisionRecordCreate, DecisionRecordUpdate, DecisionRecordResponse, DecisionListResponse
from core.auth import get_current_user
from services.db import supabase
from services.decision_memory_service import generate_and_store_decision_memory

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=DecisionRecordResponse)
def create_decision(body: DecisionRecordCreate, response: Response, user_id: str = Depends(get_current_user), x_workspace_id: str | None = Header(default=None, alias="x-workspace-id")):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Phase 4 — use /workspaces/{id}/decisions"
    # Check if a record already exists for this session
    existing = supabase.table("decision_records").select("id").eq("research_session_id", body.research_session_id).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="A decision record already exists for this research session.")

    payload = {
        "workspace_id": x_workspace_id,
        "research_session_id": body.research_session_id,
        "title": body.title,
        "status": body.status,
        "created_by": user_id
    }

    try:
        res = supabase.table("decision_records").insert(payload).execute()
        created = res.data[0]
        
        # We need to return it with the research fields joined, so we fetch it back
        return get_decision(created["id"], user_id)
    except Exception as e:
        logger.error(f"Failed to create decision record: {e}")
        raise HTTPException(status_code=500, detail="Failed to create decision record")

@router.get("", response_model=DecisionListResponse)
def list_decisions(response: Response, user_id: str = Depends(get_current_user), x_workspace_id: str | None = Header(default=None, alias="x-workspace-id")):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Phase 4 — use /workspaces/{id}/decisions"
    query = supabase.table("decision_records").select("*")
    
    if x_workspace_id:
        query = query.eq("workspace_id", x_workspace_id)
    else:
        query = query.eq("created_by", user_id)
        
    res = query.order("created_at", desc=True).execute()
    decisions = res.data
    
    if not decisions:
        return DecisionListResponse(decisions=[])
        
    # Manually join research_reports
    session_ids = [d["research_session_id"] for d in decisions]
    reports_res = supabase.table("research_reports").select(
        "session_id, question, recommendation_context, executive_summary, alternatives"
    ).in_("session_id", session_ids).execute()
    
    reports_map = {r["session_id"]: r for r in reports_res.data}
    
    for d in decisions:
        report = reports_map.get(d["research_session_id"], {})
        d.update({
            "question": report.get("question"),
            "recommendation_context": report.get("recommendation_context"),
            "executive_summary": report.get("executive_summary"),
            "alternatives": report.get("alternatives")
        })
        
    return DecisionListResponse(decisions=decisions)

@router.get("/{decision_id}", response_model=DecisionRecordResponse)
def get_decision(decision_id: str, response: Response, user_id: str = Depends(get_current_user)):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Phase 4 — use /workspaces/{id}/decisions"
    res = supabase.table("decision_records").select("*").eq("id", decision_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Decision record not found")
        
    row = res.data[0]
    
    reports_res = supabase.table("research_reports").select(
        "question, recommendation_context, executive_summary, alternatives"
    ).eq("session_id", row["research_session_id"]).execute()
    
    report = reports_res.data[0] if reports_res.data else {}
    row.update(report)
    
    return row

@router.patch("/{decision_id}", response_model=DecisionRecordResponse)
def update_decision_status(decision_id: str, body: DecisionRecordUpdate, response: Response, background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user)):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "Phase 4 — use /workspaces/{id}/decisions"
    payload = {"status": body.status}
    if body.title:
        payload["title"] = body.title
        
    res = supabase.table("decision_records").update(payload).eq("id", decision_id).eq("created_by", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Decision record not found or unauthorized")
        
    # If approved or implemented, trigger the persistent memory generation!
    if body.status in ["APPROVED", "IMPLEMENTED"]:
        background_tasks.add_task(generate_and_store_decision_memory, decision_id, user_id)
        
    return get_decision(decision_id, user_id)
