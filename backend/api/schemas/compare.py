from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class CompareRequest(BaseModel):
    session_a: str
    session_b: str

class StructuralDiff(BaseModel):
    recommendation: str
    tradeoffs: str
    alternatives: str
    confidence: str

class ComparisonOutput(BaseModel):
    id: str
    session_a: str
    session_b: str
    structural_diff: StructuralDiff
    decision_evolution: str
    impact_summary: str
    created_at: str

class CompareResponse(BaseModel):
    comparison_id: str
    comparison: ComparisonOutput

class GetComparisonResponse(BaseModel):
    comparison: ComparisonOutput

class SaveCompareRequest(BaseModel):
    comparison_id: str

class SaveCompareResponse(BaseModel):
    saved: bool

class SuggestionItem(BaseModel):
    session_id: str
    question: str
    created_at: str
    score: float

class SuggestionsResponse(BaseModel):
    suggestions: List[SuggestionItem]
