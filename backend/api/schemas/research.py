from pydantic import BaseModel, Field
from typing import Optional


class ResearchRequest(BaseModel):
    question: str = Field(..., min_length=10, max_length=1000)


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
