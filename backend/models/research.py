from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ConfidenceScore(BaseModel):
    evidence_coverage: float = 0.0
    source_quality: float = 0.0
    contradiction_risk: float = 0.0
    decision_confidence: float = 0.0


class ResearchSession(BaseModel):
    id: str = ""
    question: str
    status: str = "draft"  # draft | partial | complete | failed
    version: int = 1
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DecisionDocument(BaseModel):
    id: str = ""
    session_id: str = ""
    question: str
    executive_summary: str = ""
    recommendation_context: str = ""
    tradeoffs: str = ""
    alternatives: str = ""
    confidence: ConfidenceScore = ConfidenceScore()
    version: int = 1
    created_at: Optional[datetime] = None


class ResearchJob(BaseModel):
    id: str = ""
    session_id: str
    status: str = "queued"  # queued | running | completed | failed
    progress: int = 0
    step: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
