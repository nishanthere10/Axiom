import json
import logging
from core.config import settings
from agents.state.research_state import ResearchState
from services.llm_provider import generate_chat_completion

logger = logging.getLogger(__name__)


def generate_decision(state: ResearchState) -> dict:
    """
    Node 2: Generates the full engineering decision — recommendation context,
    tradeoffs, and alternatives — using the question and executive summary.
    """
    question = state["question"]
    summary = state["summary"]
    evidence = state.get("evidence", [])
    memory_context = state.get("memory_context", {})
    github_context = memory_context.get("github_context", [])
    
    # Format evidence for the prompt
    evidence_text = "\n\n".join(
        f"[Source {i+1}]: {e['title']} - {e['claim']}" 
        for i, e in enumerate(evidence)
    )

    # Format repository context
    github_text = "\n\n".join(
        f"[Source: {chunk.get('file_path', 'unknown')} | {chunk.get('repository', 'unknown')}]\n{chunk.get('raw_snippet') or chunk.get('content', '')}"
        for chunk in github_context
    )

    prompt = f"""You are a distinguished Principal Software Engineer. Based on the technical question, analysis, and the provided EVIDENCE and REPOSITORY CONTEXT, generate a highly scannable, expert-level decision document. 
Do not use huge text blocks. Use bullet points and bold text to make it readable at a glance. Prioritize context-rich quality over quantity.
CRITICAL: You MUST base your decision on the Evidence and Repository Context provided. You must cite your sources (e.g. "[Source 1]" or "[Source: file_path]") when making claims.

Question: {question}

Analysis: {summary}

Evidence:
{evidence_text if evidence else "No external evidence provided."}

Repository Context:
{github_text if github_context else "No repository context provided."}

Return a JSON object with exactly these keys. The value for each key MUST be a single Markdown string, NOT nested JSON objects or arrays:
- "reasoning_scratchpad": A string where you actively debate the pros and cons, resolve contradictions in the evidence, and weigh tradeoffs mathematically against the repository context. This is your Chain-of-Thought space to reach the best conclusion. Do this FIRST.
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

    # Critical node — let exceptions propagate to fail the pipeline
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

    return {
        "reasoning": enforce_string(content.get("reasoning_scratchpad", "No reasoning provided.")),
        "recommendation": enforce_string(content.get("recommendation_context", "Could not generate recommendation.")),
        "tradeoffs": enforce_string(content.get("tradeoffs", "Could not generate tradeoffs.")),
        "alternatives": enforce_string(content.get("alternatives", "Could not generate alternatives.")),
        "status": "generated",
    }
