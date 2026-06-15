import json
import logging
from services.llm_provider import generate_chat_completion
from agents.state.research_state import ResearchState

logger = logging.getLogger(__name__)


def build_confidence(state: ResearchState) -> dict:
    """
    Node 3: Scores the confidence of the generated decision across 4 dimensions.
    The system must never claim certainty n— scores reflect evidence quality.
    """
    recommendation = state["recommendation"]
    tradeoffs = state["tradeoffs"]
    consensus = state.get("consensus", "Unknown")

    prompt = f"""You are an epistemically careful engineering analyst. 
Evaluate the confidence of this technical recommendation based on the tradeoffs identified and the external evidence consensus.
The system must NEVER claim certainty. All scores should reflect genuine uncertainty.
Strong consensus should increase confidence, while conflicting or weak consensus should lower it.

Evidence Consensus: {consensus}

Recommendation: {str(recommendation)[:1000]}

Tradeoffs: {str(tradeoffs)[:800]}

Return a JSON object with exactly these keys and float values between 0.0 and 1.0:
- "evidence_coverage": How much of the problem space is covered by available evidence (0 = unknown territory, 1 = well-documented area)
- "source_quality": Quality and reliability of the underlying knowledge (0 = speculative, 1 = battle-tested)  
- "contradiction_risk": Risk of contradictions in the recommendation (0 = highly consistent, 1 = contradictory)
- "decision_confidence": Overall confidence in the decision (0 = very uncertain, 1 = very confident — never use 1.0)

Return only valid JSON."""

    # Critical node — let exceptions propagate to fail the pipeline
    response = generate_chat_completion(
        messages=[
            {"role": "system", "content": "You are a calibrated uncertainty estimator. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=300,
    )
    confidence_raw = json.loads(response.choices[0].message.content)

    valid_keys = {"evidence_coverage", "source_quality", "contradiction_risk", "decision_confidence"}
    clamped = {}
    for k in valid_keys:
        try:
            clamped[k] = max(0.0, min(float(confidence_raw.get(k, 0.5)), 0.95))
        except (ValueError, TypeError):
            clamped[k] = 0.5  # safe default if LLM returns non-numeric

    return {"confidence": clamped, "status": "evaluated"}
