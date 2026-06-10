from typing import TypedDict, Dict, Any, Optional, Annotated

def override_status(left: str | None, right: str | None) -> str | None:
    """Always keep the most recent status update during concurrent node execution."""
    return right if right is not None else left

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
    
    visual_specs: Optional[list[Dict[str, Any]]]
    visuals: Optional[list[Dict[str, Any]]]
    
    retrieved_memories: Optional[list[Dict[str, Any]]]
    memory_context: Optional[Dict[str, Any]]
    
    status: Annotated[str | None, override_status]
