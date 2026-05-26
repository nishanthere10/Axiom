import json
from groq import Groq
from core.config import settings
from agents.state.research_state import ResearchState

_client = Groq(api_key=settings.GROQ_API_KEY)
_MODEL = "llama-3.3-70b-versatile"


def generate_decision(state: ResearchState) -> dict:
    """
    Node 2: Generates the full engineering decision — recommendation context,
    tradeoffs, and alternatives — using the question and executive summary.
    """
    question = state["question"]
    summary = state["summary"]

    prompt = f"""You are a distinguished Principal Software Engineer. Based on the technical question and analysis, generate a highly scannable, expert-level decision document. Do not use huge text blocks. Use bullet points and bold text to make it readable at a glance. Prioritize context-rich quality over quantity.

Question: {question}

Analysis: {summary}

Return a JSON object with exactly these keys. The value for each key MUST be a single Markdown string, NOT nested JSON objects or arrays:
- "recommendation_context": A Markdown string containing a highly scannable recommendation. Use bullet points to highlight EXACTLY why this approach is best. Keep sentences very short and punchy. Include a brief code/config snippet if it helps clarity.
- "tradeoffs": A Markdown string containing a rigorous but scannable analysis. Use bulleted lists for pros, cons, and risks. Highlight key metrics (latency, scale) in bold. No wall of text.
- "alternatives": A Markdown string containing a bulleted list of 1-2 viable alternatives. Explain in one sentence when they apply and why they were rejected here.

Return only valid JSON. Ensure all strings correctly escape quotes and newlines so the JSON remains valid. DO NOT use nested arrays or objects for the values."""

    response = _client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": "You are an elite Principal Engineer. You write context-rich, highly scannable technical docs. Rely heavily on bullet points and bold text for at-a-glance readability. Zero fluff. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
        max_tokens=6000,
    )

    content = json.loads(response.choices[0].message.content)
    
    def enforce_string(val):
        if isinstance(val, list):
            return "\n".join(f"- {str(v)}" for v in val)
        if isinstance(val, dict):
            return "\n".join(f"- **{k}**: {v}" for k, v in val.items())
        return str(val)

    return {
        "recommendation": enforce_string(content.get("recommendation_context", "")),
        "tradeoffs": enforce_string(content.get("tradeoffs", "")),
        "alternatives": enforce_string(content.get("alternatives", "")),
        "status": "generated",
    }
