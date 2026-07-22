import logging
from typing import Any, Dict
from services.llm_provider import get_async_instructor_client
from api.schemas.visuals import VisualSpecResponse

logger = logging.getLogger(__name__)

# Max evidence items passed to the LLM. Top items by trust_score are used.
# Keeping this low prevents token blowout on queries with many sources.
_MAX_EVIDENCE_ITEMS = 5

# Hard cap on output tokens. Visual specs are structured JSON — 2048 is ample.
_MAX_OUTPUT_TOKENS = 2048

# Smaller fast model for structured extraction — saves ~80% TPM vs llama-3.3-70b-versatile.
# This node is a Pydantic extraction task, not a reasoning task, so 8B is sufficient.
_VISUAL_MODEL = "groq/llama-3.1-8b-instant"


def _trim_evidence(evidence: list[dict], max_items: int) -> list[dict]:
    """Return top-N evidence items by trust_score, stripped of heavy fields."""
    scored = sorted(evidence, key=lambda e: e.get("trust_score", 0.0), reverse=True)
    trimmed = []
    for e in scored[:max_items]:
        trimmed.append({
            "title":       e.get("title", "Source"),
            "claim":       e.get("claim", ""),
            "trust_score": e.get("trust_score"),
            "metrics":     e.get("metrics", ""),
            "url":         e.get("url", ""),
        })
    return trimmed


def _fmt_evidence(e: dict) -> str:
    parts = [f"[{e.get('title', 'Source')}]"]
    if e.get("claim"):
        parts.append(e["claim"])
    if e.get("metrics"):
        parts.append(f"(metrics: {e['metrics']})")
    if e.get("trust_score") is not None:
        parts.append(f"(score: {e['trust_score']:.2f})")
    if e.get("url"):
        parts.append(f"<{e['url']}>")
    return " ".join(parts)


async def generate_visual_spec(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates 1-3 decision-support visual specifications using structured output.
    State is trimmed before LLM call to stay within Groq TPM limits.
    Falls back to empty visuals on any error (non-fatal node).
    """
    # ── Extract only what the LLM needs (state trimming) ──
    question       = state.get("question", "")
    summary        = state.get("summary", "")
    recommendation = state.get("recommendation", "")
    tradeoffs      = state.get("tradeoffs", "")
    alternatives   = state.get("alternatives", "")
    confidence     = state.get("confidence", {})
    raw_evidence   = state.get("evidence", [])

    # Trim evidence: top-5 by trust_score, drop heavy fields (embeddings, raw_content, etc.)
    evidence = _trim_evidence(raw_evidence, _MAX_EVIDENCE_ITEMS)

    evidence_text   = "\n".join(_fmt_evidence(e) for e in evidence) or "No external evidence."
    confidence_text = "\n".join(f"  {k}: {v}" for k, v in confidence.items()) or "Not available."

    # ── Compressed prompt (~60% shorter than original) ──
    prompt = f"""You are a technical architect generating decision-support visuals.

DECISION CONTEXT:
Q: {question}
SUMMARY: {summary}
RECOMMENDATION: {recommendation}
TRADEOFFS: {tradeoffs}
ALTERNATIVES: {alternatives}
CONFIDENCE: {confidence_text}
EVIDENCE ({len(evidence)} of {len(raw_evidence)} top sources):
{evidence_text}

TASK: Generate 1-3 structured visuals. Use exact tech names from context — no placeholders.

RULES:
- At least 1 visual for any architecture/system/multi-step decision. Empty only for trivial topics.
- Max 3 visuals, no duplicate types.
- description field REQUIRED on every node — must include a concrete number or metric.

DECISION_TREE: 6-10 nodes. label ≤5 words (real tech). node_type: root/decision/outcome/leaf. edge label = quantitative condition.
ARCHITECTURE_DIAGRAM: 6-12 nodes, full data path (client→storage, cache, async layers). spec = 1-line key metric on node face.
SUMMARY_CARD: 5-8 highlights — at least 2 metrics (real numbers), 2 tradeoffs, 1 warning, 1 recommendation."""

    try:
        client = get_async_instructor_client()
        response: VisualSpecResponse = await client.chat.completions.create(
            model=_VISUAL_MODEL,
            response_model=VisualSpecResponse,
            max_retries=2,
            max_tokens=_MAX_OUTPUT_TOKENS,
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        visuals = [v.model_dump() for v in response.visuals]
        logger.debug("generate_visual_spec: produced %d visuals via %s", len(visuals), _VISUAL_MODEL)
        return {"visual_specs": visuals}
    except Exception as e:
        logger.warning("Visual generation failed (non-fatal): %s", e)
        return {"visual_specs": []}


