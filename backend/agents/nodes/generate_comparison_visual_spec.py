from typing import Any, Dict
from pydantic import BaseModel
import instructor
from services.llm_provider import get_instructor_client
from api.schemas.visuals import VisualSpecResponse
from core.config import settings

def generate_comparison_visual_spec(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates relevance and conditionally generates visual specifications (up to 3)
    to compare two different research sessions.
    Returns an empty array if visuals are unnecessary.
    """
    diff = state.get("structural_diff", {})
    decision_evolution = state.get("decision_evolution", {})
    impact_summary = state.get("impact_summary", {})
    
    # We will use the structured output format with Instructor and Groq
    client = get_instructor_client()
    
    prompt = f"""
    You are an expert technical architect and visual designer.
    Your task is to generate visual representations (Architecture Diagrams, Summary Cards, or Decision Trees) 
    that help clarify the DIFFERENCE between two technical options being compared.

    RULES:
    1. You MUST generate at least one visual if the comparison involves architecture, system design, or clear tradeoffs. Only return an empty array for trivial or non-technical topics.
    2. Do NOT generate more than 3 visuals.
    3. Do NOT generate duplicate visual types.
    4. For Architecture Diagrams: Show a side-by-side or unified architecture comparing Option A and Option B if possible.
       - Start with "graph TD" (top-down) for hierarchy, or "graph LR" (left-right) for pipelines.
       - MAX 8 nodes total. Group related nodes inside `subgraph` blocks for clarity (e.g. `subgraph Option A`).
       - Node labels MUST be short (max 4-5 words). DO NOT write paragraphs inside nodes.
       - Use ONLY these arrow formats: A --> B, A -->|label text| B, A --- B.
       - CRITICAL MERMAID SYNTAX: Never use -->|text|> for labeled arrows. Never use nested shape definitions like NodeID[A(Label)].
       - If a label contains spaces or special characters, you MUST enclose it in double quotes: NodeID["Label Text"].
       - Do NOT wrap in markdown code blocks.
    5. For Decision Trees: Map out the conditional logic ("If condition X, use Option A."). MAX 8 nodes. Keep labels short (max 4-5 words).
    6. For Summary Cards: Summarize the final verdict, which option wins on which metric, and the core tradeoff.

    STRUCTURAL DIFF:
    {diff}

    DECISION EVOLUTION:
    {decision_evolution}

    IMPACT SUMMARY:
    {impact_summary}
    """
    
    try:
        response: VisualSpecResponse = client.chat.completions.create(
            model="groq/llama-3.3-70b-versatile",
            response_model=VisualSpecResponse,
            max_retries=3,
            parallel_tool_calls=False,
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        return {"visual_specs": [v.model_dump() for v in response.visuals], "status": "visual_specs_generated"}
    except Exception as e:
        print(f"Comparison Visual Generation Error: {e}")
        return {"visual_specs": [], "status": "visual_specs_failed"}
