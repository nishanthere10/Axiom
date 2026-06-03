import json
from core.config import settings
from agents.state.research_state import ResearchState
from services.llm_provider import generate_chat_completion


def generate_decision(state: ResearchState) -> dict:
    """
    Node 2: Generates the full engineering decision — recommendation context,
    tradeoffs, and alternatives — using the question and executive summary.
    """
    question = state["question"]
    summary = state["summary"]
    evidence = state.get("evidence", [])
    
    # Format evidence for the prompt
    evidence_text = "\n\n".join(
        f"[Source {i+1}]: {e['title']} - {e['claim']}" 
        for i, e in enumerate(evidence)
    )

    prompt = f"""You are a distinguished Principal Software Engineer. Based on the technical question, analysis, and the provided EVIDENCE, generate a highly scannable, expert-level decision document. 
Do not use huge text blocks. Use bullet points and bold text to make it readable at a glance. Prioritize context-rich quality over quantity.
CRITICAL: You MUST base your decision on the Evidence provided. You must cite your sources (e.g. "[Source 1]") when making claims.

Question: {question}

Analysis: {summary}

Evidence:
{evidence_text if evidence else "No external evidence provided. Rely on general knowledge."}

Return a JSON object with exactly these keys. The value for each key MUST be a single Markdown string, NOT nested JSON objects or arrays:
- "recommendation_context": A Markdown string containing a highly scannable recommendation. Use bullet points to highlight EXACTLY why this approach is best. Keep sentences very short and punchy. Include a brief code/config snippet if it helps clarity.
- "tradeoffs": A Markdown string containing a rigorous but scannable analysis. Use bulleted lists for pros, cons, and risks. Highlight key metrics (latency, scale) in bold. No wall of text.
- "alternatives": A Markdown string containing a bulleted list of 1-2 viable alternatives. Explain in one sentence when they apply and why they were rejected here.

Return only valid JSON. Ensure all strings correctly escape quotes and newlines so the JSON remains valid. DO NOT use nested arrays or objects for the values."""

    def enforce_string(val):
        if isinstance(val, list):
            return "\n".join(f"- {str(v)}" for v in val)
        if isinstance(val, dict):
            return "\n".join(f"- **{k}**: {v}" for k, v in val.items())
        return str(val)

    try:
        response = generate_chat_completion(
            messages=[
                {"role": "system", "content": "You are an elite Principal Engineer. You write context-rich, highly scannable technical docs. Rely heavily on bullet points and bold text for at-a-glance readability. Zero fluff. Return only valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
            max_tokens=6000,
        )
        content = json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error in generate_decision: {e}")
        content = {}

    return {
        "recommendation": enforce_string(content.get("recommendation_context", "Could not generate recommendation.")),
        "tradeoffs": enforce_string(content.get("tradeoffs", "Could not generate tradeoffs.")),
        "alternatives": enforce_string(content.get("alternatives", "Could not generate alternatives.")),
        "status": "generated",
    }
