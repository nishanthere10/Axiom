from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime

MemoryType = Literal["decision", "comparison", "evidence", "visual", "preference"]
MemoryScope = Literal["temporary", "permanent"]

class MemoryItemCreate(BaseModel):
    memory_type: MemoryType
    source_id: str
    source_type: str
    summary: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    scope: MemoryScope = "temporary"
    expires_at: Optional[datetime] = None

class MemoryItemResponse(BaseModel):
    id: str
    memory_type: MemoryType
    source_id: str
    source_type: str
    summary: str
    metadata: Dict[str, Any]
    scope: MemoryScope
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]

class PreferenceInsight(BaseModel):
    type: Literal["preference_candidate"] = "preference_candidate"
    value: str = Field(description="The preferred technology, pattern, or constraint")
    reason: str = Field(description="Why this appears to be a preference based on historical memory")

class MemoryContextSchema(BaseModel):
    preferences: List[PreferenceInsight] = Field(description="Any detected preferences or leanings")
    historical_patterns: List[str] = Field(description="Recurring patterns across past decisions")
    related_decisions: List[str] = Field(description="Directly related historical decisions that inform the current query")
    consistency_warnings: List[str] = Field(description="Warnings if the current proposed query contradicts a strongly held historical decision")
