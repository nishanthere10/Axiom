from typing import TypedDict


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
    
    status: str
