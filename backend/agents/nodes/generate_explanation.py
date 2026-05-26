import json
from groq import Groq
from core.config import settings
from agents.state.comparison_state import ComparisonState

_client = Groq(api_key=settings.GROQ_API_KEY)
_MODEL = "llama-3.3-70b-versatile"

_SYSTEM_PROMPT = """You are an elite Principal Software Architect performing an architectural teardown of how a system design evolved.
Your goal is to explain the engineering WHY behind the decision evolution. 

Return ONLY a valid JSON object with EXACTLY the following schema:
{
    "verdict": "One short, bold sentence summarizing the shift (e.g. 'Shifted from PostgreSQL to DynamoDB due to scale.')",
    "key_changes": [
        {
            "field": "Recommendation" | "Tradeoffs" | "Alternatives" | "Confidence",
            "before": "Extremely brief summary of before state (3-5 words)",
            "after": "Extremely brief summary of after state (3-5 words)",
            "change_type": "major" | "minor" | "improved" | "unchanged"
        }
    ],
    "reasoning": "A short, highly scannable explanation using bullet points."
}
"""

def generate_explanation(state: ComparisonState) -> dict:
    """
    Node 4: Uses LLM to explain the decision evolution.
    """
    diff_text = json.dumps(state["structural_diff"], indent=2)
    q = state["document_b"].get("question", "Unknown")
    
    prompt = f"Question: {q}\n\nStructural Diff:\n{diff_text}\n\nGenerate the structured architectural evolution."
    
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
        evolution = parsed
    except Exception:
        evolution = {
            "verdict": "Error parsing LLM output.",
            "key_changes": [],
            "reasoning": "Could not parse the reasoning."
        }
        
    return {
        "decision_evolution": evolution,
        "status": "explanation_generated"
    }
