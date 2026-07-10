from typing import TypedDict, Annotated

def override_status(left: str | None, right: str | None) -> str | None:
    """Always keep the most recent status update during concurrent node execution."""
    return right if right is not None else left

class ResearchState(TypedDict):
    """Represents the state of the LangGraph research pipeline."""
    question: str
    user_id: str
    sub_questions: list[str]
    summary: str
    constraints: list[str]
    reasoning: str
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
    github_context: list[dict]
    
    scored_memories: list[dict]
    scored_github: list[dict]
    injected_memory_count: int
    injected_github_count: int
    dropped_context_count: int
    warnings: list[str]
    
    status: Annotated[str | None, override_status]
