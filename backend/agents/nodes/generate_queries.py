from agents.state.research_state import ResearchState
from groq import Groq
from core.config import settings
import json

_client = Groq(api_key=settings.GROQ_API_KEY)
_MODEL = "llama-3.3-70b-versatile"

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
        response = _client.chat.completions.create(
            model=_MODEL,
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
