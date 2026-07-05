from pydantic import BaseModel, Field
from typing import Optional, Any, Dict

class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=1000)
    force_refresh: bool = False
    project_id: Optional[str] = None


class DecisionDocument(BaseModel):
    id: str
    session_id: str
    question: str
    summary: str
    recommendation_context: str
    tradeoffs: str
    alternatives: str
    confidence: Dict[str, float]
    evidence: Optional[Any] = []
    consensus: Optional[str] = ""
    evidence_generated_at: Optional[str] = None
    visuals: Optional[Any] = []
    visuals_generated_at: Optional[str] = None
    created_at: str


class ResearchResponse(BaseModel):
    session_id: str
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    status: str
    progress: int
    step: str


class SessionDocumentResponse(BaseModel):
    document: Optional[dict]

class SessionHistoryItem(BaseModel):
    id: str
    question: str
    created_at: str

class SessionHistoryResponse(BaseModel):
    sessions: list[SessionHistoryItem]

class RegenerateVisualsRequest(BaseModel):
    session_id: str

class RegenerateVisualsResponse(BaseModel):
    visuals: list[Any]
