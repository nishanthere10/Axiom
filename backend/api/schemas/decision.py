from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class DecisionRecordCreate(BaseModel):
    research_session_id: str
    title: str
    status: str = "PROPOSED"

class DecisionRecordUpdate(BaseModel):
    status: str
    title: Optional[str] = None

class DecisionRecordResponse(BaseModel):
    id: str
    workspace_id: Optional[str] = None
    research_session_id: str
    title: str
    status: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    
    # Joined fields from research_reports
    question: Optional[str] = None
    recommendation_context: Optional[str] = None
    executive_summary: Optional[str] = None
    alternatives: Optional[str] = None
    evidence: Optional[List[Dict[str, Any]]] = None

class DecisionListResponse(BaseModel):
    decisions: List[DecisionRecordResponse]
