from agents.state.research_state import ResearchState
from groq import Groq
from core.config import settings
import json

_client = Groq(api_key=settings.GROQ_API_KEY)
_MODEL = "llama-3.3-70b-versatile"

def canonicalize_topic(state: ResearchState) -> dict:
    """
    Node: Generates a stable canonical slug for the topic to use as a cache key.
    """
    question = state["question"]
    
    prompt = f"""Convert this technical research question into a canonical, SEO-style URL slug.
Focus only on the core technologies, concepts, or problem space.
Drop stop words. Use lowercase alphanumeric and hyphens only.
Examples:
"What is the difference between LangGraph and CrewAI?" -> "langgraph-vs-crewai"
"Should I use Postgres or DynamoDB for a read-heavy app?" -> "postgres-vs-dynamodb-read-heavy"

Question: {question}

Return ONLY a JSON object with this exact schema:
{{
    "slug": "canonical-slug-here"
}}"""

    try:
        response = _client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=50
        )
        content = json.loads(response.choices[0].message.content)
        slug = content.get("slug", "unknown-topic").lower().replace(" ", "-")
    except Exception:
        # Fallback to simple hash-like slug if LLM fails
        slug = "fallback-" + str(hash(question))
        
    return {
        "canonical_slug": slug,
        "status": "canonicalized"
    }
