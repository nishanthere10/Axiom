import json
from langchain_core.messages import SystemMessage, HumanMessage
from agents.state.comparison_state import ComparisonState
from agents.models import get_llm

_SYSTEM_PROMPT = """You are a senior engineering manager.
Given the decision evolution and diff, describe the IMPACT of this change.
What are the recommended actions? Is a migration needed? What follow-up steps should be taken?

Return ONLY a valid JSON object with the following schema:
{
    "impact_summary": "Detailed impact and recommended actions..."
}
"""

def generate_impact(state: ComparisonState) -> dict:
    """
    Node 5: Uses LLM to generate the impact summary.
    """
    evolution = state["decision_evolution"]
    
    prompt = f"Decision Evolution:\n{evolution}\n\nGenerate impact summary."
    
    llm = get_llm().with_config({"response_format": {"type": "json_object"}})
    response = llm.invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])
    
    try:
        parsed = json.loads(response.content)
        impact = parsed.get("impact_summary", "Impact could not be parsed.")
    except Exception:
        impact = "Error parsing LLM output."
        
    return {
        "impact_summary": impact,
        "status": "impact_generated"
    }
