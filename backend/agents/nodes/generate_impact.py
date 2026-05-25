import json
from groq import Groq
from core.config import settings
from agents.state.comparison_state import ComparisonState

_client = Groq(api_key=settings.GROQ_API_KEY)
_MODEL = "llama-3.3-70b-versatile"

_SYSTEM_PROMPT = """You are an elite Principal Software Architect analyzing the fallout of a major architectural shift.
Given the decision evolution and structural diff, describe the rigorous engineering IMPACT of this change.
Do not use huge text blocks. You MUST use bullet points and bold text to make it readable at a glance. Prioritize context-rich quality over quantity. Keep sentences very short and punchy.

Return ONLY a valid JSON object with the following schema:
{
    "impact_summary": "Highly scannable explanation of the impact and migration paths using bullet points..."
}
"""

def generate_impact(state: ComparisonState) -> dict:
    """
    Node 5: Uses LLM to generate the impact summary.
    """
    evolution = state["decision_evolution"]
    
    prompt = f"Decision Evolution:\n{evolution}\n\nGenerate a highly scannable impact summary detailing migration strategies. Rely heavily on bullet points and bold text."
    
    response = _client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"},
        temperature=0.3,
        max_tokens=4000,
    )
    
    try:
        content = response.choices[0].message.content
        parsed = json.loads(content)
        impact = parsed.get("impact_summary", "Impact could not be parsed.")
    except Exception:
        impact = "Error parsing LLM output."
        
    return {
        "impact_summary": impact,
        "status": "impact_generated"
    }
