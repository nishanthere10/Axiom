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

    prompt = f"""You are a senior engineering decision-maker. Based on the technical question and its analysis, generate a comprehensive decision document.

Question: {question}

Analysis: {summary}

Return a JSON object with exactly these keys:
- "recommendation_context": A detailed 3-5 paragraph recommendation explaining the best approach, why it fits, and under what conditions it applies. No markdown.
- "tradeoffs": A thorough analysis of the key tradeoffs (pros, cons, risks). Write as structured plain text paragraphs, not bullet points.
- "alternatives": Description of 2-3 viable alternative approaches, when they make sense, and how they compare. Plain text.

Return only valid JSON with those three keys."""

    response = _client.chat.completions.create(
        model=_MODEL,
        messages=[
            {"role": "system", "content": "You are an expert software engineering advisor. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
        max_tokens=2500,
    )

    content = json.loads(response.choices[0].message.content)

    return {
        "recommendation": content.get("recommendation_context", ""),
        "tradeoffs": content.get("tradeoffs", ""),
        "alternatives": content.get("alternatives", ""),
        "status": "generated",
    }
