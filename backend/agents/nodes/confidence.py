import json
from groq import Groq
from core.config import settings
from agents.state.research_state import ResearchState

_client = Groq(api_key=settings.GROQ_API_KEY)
_MODEL = "llama-3.3-70b-versatile"


def build_confidence(state: ResearchState) -> dict:
    """
    Node 3: Scores the confidence of the generated decision across 4 dimensions.
    The system must never claim certainty — scores reflect evidence quality.
    """
    recommendation = state["recommendation"]
    tradeoffs = state["tradeoffs"]

    prompt = f"""You are an epistemically careful engineering analyst. 
Evaluate the confidence of this technical recommendation based on the tradeoffs identified.
The system must NEVER claim certainty. All scores should reflect genuine uncertainty.

Recommendation: {recommendation[:1000]}

Tradeoffs: {tradeoffs[:800]}

Return a JSON object with exactly these keys and float values between 0.0 and 1.0:
- "evidence_coverage": How much of the problem space is covered by available evidence (0 = unknown territory, 1 = well-documented area)
- "source_quality": Quality and reliability of the underlying knowledge (0 = speculative, 1 = battle-tested)  
- "contradiction_risk": Risk of contradictions in the recommendation (0 = highly consistent, 1 = contradictory)
- "decision_confidence": Overall confidence in the decision (0 = very uncertain, 1 = very confident — never use 1.0)

Return only valid JSON."""

    response = _client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": "You are a calibrated uncertainty estimator. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=300,
    )

    confidence = json.loads(response.choices[0].message.content)

    # Clamp all values to [0.0, 0.95] — system never claims certainty
    clamped = {
        k: max(0.0, min(float(v), 0.95))
        for k, v in confidence.items()
        if k in {"evidence_coverage", "source_quality", "contradiction_risk", "decision_confidence"}
    }

    return {"confidence": clamped, "status": "evaluated"}
