from agents.state.research_state import ResearchState
from services.llm_provider import generate_chat_completion
from core.config import settings
import json


def generate_queries(state: ResearchState) -> dict:
    """
    Node: Generates search queries to collect evidence.
    """
    question = state["question"]
    summary = state.get("summary", "")
    
    prompt = f"""You are a research engineer. Generate 3 to 5 highly effective web search queries to collect evidence that answers the following technical question.
Focus on finding architectural comparisons, tradeoffs, and industry consensus.

Question: {question}
Context: {summary}

Return ONLY a JSON object with this exact schema:
{{
    "queries": ["query 1", "query 2", "query 3"]
}}"""

    try:
        response = generate_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=200
        )
        content = json.loads(response.choices[0].message.content)
        queries = content.get("queries", [])
    except Exception:
        queries = [question]
        
    return {
        "queries": queries,
        "status": "queries_generated"
    }
