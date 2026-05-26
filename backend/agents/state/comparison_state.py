from typing import TypedDict, Dict, Any, Optional

class ComparisonState(TypedDict):
    session_a_id: str
    session_b_id: str
    
    document_a: Optional[Dict[str, Any]]
    document_b: Optional[Dict[str, Any]]
    
    normalized_a: Optional[Dict[str, Any]]
    normalized_b: Optional[Dict[str, Any]]
    
    structural_diff: Optional[Dict[str, str]]
    decision_evolution: Optional[Dict[str, Any]]
    impact_summary: Optional[Dict[str, Any]]
    
    status: str
