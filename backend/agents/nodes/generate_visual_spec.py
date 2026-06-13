import logging
from typing import Any, Dict
from pydantic import BaseModel
import instructor
from services.llm_provider import get_instructor_client
from api.schemas.visuals import VisualSpecResponse

logger = logging.getLogger(__name__)

def generate_visual_spec(state: Dict[str, Any]) -> Dict[str, Any]:
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
    client = get_instructor_client()
    
    # Build a rich evidence summary for the prompt
    evidence_text = "\n".join(
        f"- [{e.get('title', 'Source')}]: {e.get('claim', '')}" for e in evidence
    ) if evidence else "No external evidence."

    prompt = f"""
    You are an expert technical architect and visual designer.
    Your task is to generate visual representations (Decision Trees, Architecture Diagrams, or Summary Cards) 
    that help clarify the following architectural decision.

    RULES:
    1. You MUST generate at least one visual if the topic involves architecture, system design, or multi-step decisions. Only return an empty array for trivial or non-technical topics.
    2. Do NOT generate more than 3 visuals.
    3. Do NOT generate duplicate visual types.
    4. For Decision Trees: Map out conditional logic cleanly. MAX 8 nodes to prevent clutter. Keep labels short (max 4-5 words).
    5. For Architecture Diagrams: Provide a structured JSON layout.
       - Create an array of `nodes` representing system components. Keep labels short.
       - Use `type: "custom"` for all nodes.
       - Create an array of `edges` representing data flow or connections between nodes.
       - Set `animated: true` on edges if representing active data flow.
       - Use `group` on nodes to cluster related components under a parent node.
    6. For Summary Cards: Summarize the final recommendation, confidence, and consensus.

    QUESTION:
    {question}

    EXECUTIVE SUMMARY:
    {summary}

    RECOMMENDATION:
    {recommendation}

    TRADEOFFS:
    {tradeoffs}

    ALTERNATIVES:
    {alternatives}

    CONFIDENCE SCORES:
    {confidence}
    
    EVIDENCE:
    {evidence_text}
    """
    
    try:
        # Use Nvidia Nemotron for visual architecture structures
        response: VisualSpecResponse = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            response_model=VisualSpecResponse,
            max_retries=3,
            parallel_tool_calls=False,
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        return {"visual_specs": [v.model_dump() for v in response.visuals]}
    except Exception as e:
        logger.warning("Visual Generation Error (non-fatal): %s", e)
        # Graceful fallback: return no visuals
        return {"visual_specs": []}
