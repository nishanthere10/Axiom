import json
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state.comparison_state import ComparisonState
from agents.models import get_llm

_SYSTEM_PROMPT = """You are a senior engineering manager comparing two historical architecture decisions.
Your goal is to explain WHY the decision evolved, focusing on the reasoning, tradeoffs, and changes in confidence.
Do NOT repeat the exact diff. Provide a synthesized narrative of the evolution.

Return ONLY a valid JSON object with the following schema:
{
    "decision_evolution": "Detailed explanation of why the decision evolved between the two sessions..."
}
"""

def generate_explanation(state: ComparisonState) -> dict:
    """
    Node 4: Uses LLM to explain the decision evolution.
    """
    diff_text = json.dumps(state["structural_diff"], indent=2)
    q = state["document_b"].get("question", "Unknown")
    
    prompt = f"Question: {q}\n\nStructural Diff:\n{diff_text}\n\nExplain the decision evolution."
    
    llm = get_llm().with_config({"response_format": {"type": "json_object"}})
    response = llm.invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])
    
    try:
        parsed = json.loads(response.content)
        evolution = parsed.get("decision_evolution", "Evolution could not be parsed.")
    except Exception:
        evolution = "Error parsing LLM output."
        
    return {
        "decision_evolution": evolution,
        "status": "explanation_generated"
    }
