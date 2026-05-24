from typing import TypedDict


class ResearchState(TypedDict):
    question: str
    summary: str        # executive_summary produced by decompose_question
    recommendation: str # recommendation_context produced by generate_decision
    tradeoffs: str
    alternatives: str
    confidence: dict    # ConfidenceScore dict produced by build_confidence
    status: str
