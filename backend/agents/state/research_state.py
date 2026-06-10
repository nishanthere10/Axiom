from typing import TypedDict, Annotated

def override_status(left: str | None, right: str | None) -> str | None:
    """Always keep the most recent status update during concurrent node execution."""
    return right if right is not None else left

class ResearchState(TypedDict):
    """Represents the state of the LangGraph research pipeline."""
    question: str
    summary: str
    recommendation: str
    tradeoffs: str
    alternatives: str
    confidence: dict    # ConfidenceScore dict produced by build_confidence
    canonical_slug: str
    queries: list[str]
    evidence: list[dict]
    consensus: str
    force_refresh: bool
    visual_specs: list[dict]
    visuals: list[dict]
    
    retrieved_memories: list[dict]
    memory_context: dict
    warnings: list[str]
    
    status: Annotated[str | None, override_status]
