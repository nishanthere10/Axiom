import json
from groq import Groq
from core.config import settings
from agents.state.comparison_state import ComparisonState

_client = Groq(api_key=settings.GROQ_API_KEY)
_MODEL = "llama-3.3-70b-versatile"

_SYSTEM_PROMPT = """You are an elite Principal Software Architect performing an architectural teardown of how a system design evolved.
Your goal is to explain the engineering WHY behind the decision evolution. 
Do not use huge text blocks. You MUST use bullet points and bold text to make it readable at a glance. Prioritize context-rich quality over quantity. Keep sentences very short and punchy.

Return ONLY a valid JSON object with the following schema:
{
    "decision_evolution": "Highly scannable explanation of the architectural evolution using bullet points..."
}
"""

def generate_explanation(state: ComparisonState) -> dict:
    """
    Node 4: Uses LLM to explain the decision evolution.
    """
    diff_text = json.dumps(state["structural_diff"], indent=2)
    q = state["document_b"].get("question", "Unknown")
    
    prompt = f"Question: {q}\n\nStructural Diff:\n{diff_text}\n\nExplain the architectural evolution between the baseline and the new decision. Rely heavily on bullet points and bold text."
    
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
        evolution = parsed.get("decision_evolution", "Evolution could not be parsed.")
    except Exception:
        evolution = "Error parsing LLM output."
        
    return {
        "decision_evolution": evolution,
        "status": "explanation_generated"
    }
