import json
import logging
from services.llm_provider import generate_chat_completion
from agents.state.comparison_state import ComparisonState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an elite Principal Software Architect analyzing the fallout of a major architectural shift.
Given the decision evolution and structural diff, describe the rigorous engineering IMPACT of this change.

Return ONLY a valid JSON object with EXACTLY the following schema:
{
    "risk_level": "low" | "medium" | "high",
    "action_items": [
        "Concise, actionable migration step 1",
        "Concise, actionable migration step 2"
    ],
    "migration_needed": true | false,
    "breaking_changes": true | false
}
"""

def generate_impact(state: ComparisonState) -> dict:
    """
    Node 5: Uses LLM to generate the impact summary.
    Critical node — let exceptions propagate.
    """
    evolution = state["decision_evolution"]
    # We pass the reasoning or verdict if it's a dict
    evo_str = json.dumps(evolution) if isinstance(evolution, dict) else str(evolution)
    
    prompt = f"Decision Evolution:\n{evo_str}\n\nGenerate the structured impact summary."
    
    # Critical node — let exceptions propagate
    response = generate_chat_completion(
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=4000,
    )
    
    content = response.choices[0].message.content
    impact = json.loads(content)
        
    return {
        "impact_summary": impact,
        "status": "impact_generated"
    }
