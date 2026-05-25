from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ComparisonModel(BaseModel):
    id: str
    session_a: str
    session_b: str
    summary: Optional[str] = None
    structural_diff: Dict[str, Any] = Field(default_factory=dict)
    decision_evolution: str = ""
    impact_summary: str = ""
    saved: bool = False
    created_at: datetime
