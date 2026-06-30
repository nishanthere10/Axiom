import logging
from typing import Any, Dict
from pydantic import BaseModel
from services.llm_provider import get_async_instructor_client
from api.schemas.visuals import VisualSpecResponse

logger = logging.getLogger(__name__)

import asyncio

async def generate_visual_spec(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates relevance and conditionally generates visual specifications (up to 3).
    Returns an empty array if visuals are unnecessary.
    """
    question = state.get("question", "")
    summary = state.get("summary", "")
    recommendation = state.get("recommendation", "")
    tradeoffs = state.get("tradeoffs", "")
    alternatives = state.get("alternatives", "")
    evidence = state.get("evidence", [])
    confidence = state.get("confidence", {})
    
    # We will use the structured output format with Instructor and Groq
    client = get_async_instructor_client()
    
    # Build a rich evidence summary — include title, claim, score, metrics AND url so LLM has real context
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

    evidence_text = "\n".join(_fmt_evidence(e) for e in evidence) if evidence else "No external evidence."
    
    # Format confidence dict as readable string
    confidence_text = "\n".join(f"  {k}: {v}" for k, v in confidence.items()) if confidence else "Not available."

    prompt = f"""You are an expert technical architect generating decision-support visuals.

CONTEXT:
QUESTION: {question}

EXECUTIVE SUMMARY:
{summary}

RECOMMENDATION:
{recommendation}

TRADEOFFS:
{tradeoffs}

ALTERNATIVES CONSIDERED:
{alternatives}

CONFIDENCE SCORES:
{confidence_text}

EVIDENCE SOURCES ({len(evidence)} items):
{evidence_text}

TASK:
Generate 1-3 structured visuals that help a software engineer understand THIS SPECIFIC decision.
All node labels, descriptions, and highlights MUST use exact technology names from the context above — never generic placeholders like "Option A", "Service X", or "Component 1".

RULES:
1. Generate AT LEAST ONE visual for any architecture, system design, or multi-step decision topic. Return empty list ONLY for trivial non-technical topics.
2. Max 3 visuals, no duplicate types. Prefer: Architecture Diagram + Decision Tree + Summary Card.
3. You MUST fill the 'description' field on EVERY node in both Decision Trees and Architecture Diagrams. It is REQUIRED.
4. Each node description MUST include at least one specific number, metric, or technology version from the evidence. Generic descriptions like 'handles requests' are unacceptable.

DECISION TREE rules:
- Generate 8-12 nodes.
- label: ≤5 words, real tech name (e.g. "Use PostgreSQL" not "Option A", "Need strong ACID?" not "Question 1")
- node_type: exactly one node must be "root", "decision" nodes are branch points, "outcome" nodes are final recommendations, "leaf" are intermediate steps
- description: REQUIRED. 1-2 sentences explaining WHY this branch/outcome. Must include a concrete number or spec.
- edge label: the quantitative condition (e.g. "Write throughput > 50k/s", "Budget <$500/mo")
- subtitle: 1 sentence saying what decision this tree navigates

ARCHITECTURE DIAGRAM rules:
- Generate 8-15 nodes covering the full data path from client to storage, including caching and async layers.
- label: real component name (e.g. "Kafka Broker", "Redis Cache", "PostgreSQL Primary")
- spec: REQUIRED. Short 1-line metric shown directly on the node face (e.g. "50k writes/s", "p99: 4ms", "3 replicas"). Use this for the single most important performance characteristic.
- description: REQUIRED. what the component does + key spec. Must include a concrete number or metric.
- node_type: pick from service/database/queue/client/gateway/cache/component
- edge label: what flows between them (e.g. "Write events", "SQL queries", "Cached responses")
- animated: true for real-time/async data flows, false for synchronous
- subtitle: 1 sentence naming the architecture pattern

SUMMARY CARD rules:
- Generate 6-10 highlights.
- summary: name the exact technology chosen and the key reason
- confidence: "High" / "Medium" / "Low" — based on evidence score data provided above
- consensus: what the industry broadly agrees on for this use case
- highlights: Must include at least 2 metrics with real numbers from evidence, 2 tradeoffs, 1 warning, 1 recommendation.
  - example metric: label="Write throughput", value="~100k ops/s at p99"
  - example warning: label="Operational Complexity", value="Requires DBA expertise for tuning at scale"
"""
    
    try:
        # Use Groq Llama for visual architecture structures.
        # NOTE: Do NOT pass mode= here — the instructor client from get_async_instructor_client()
        # is already configured with a mode via instructor.from_litellm(). Passing mode= again
        # causes: "got multiple values for keyword argument 'mode'"
        response: VisualSpecResponse = await client.chat.completions.create(
            model="deepseek-ai/deepseek-v4-pro",
            response_model=VisualSpecResponse,
            max_retries=2,
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        return {"visual_specs": [v.model_dump() for v in response.visuals]}
    except Exception as e:
        logger.warning("Visual Generation Error (non-fatal): %s", e)
        # Graceful fallback: return no visuals
        return {"visual_specs": []}

