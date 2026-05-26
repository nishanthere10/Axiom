from agents.state.research_state import ResearchState
from services.search_provider import search_tavily
from services.evidence_service import get_cached_evidence, set_cached_evidence
from groq import Groq
from core.config import settings
import json

_client = Groq(api_key=settings.GROQ_API_KEY)
_MODEL = "llama-3.3-70b-versatile"

def collect_and_score_evidence(state: ResearchState) -> dict:
    """
    Node: Fetches search results and uses LLM to extract and score claims.
    Uses cache if available unless force_refresh logic dictates otherwise.
    """
    slug = state.get("canonical_slug")
    
    # Check cache first if not forcing refresh
    if not state.get("force_refresh"):
        cached = get_cached_evidence(slug) if slug else None
        if cached:
            return {
                "evidence": cached["evidence"],
                "consensus": cached.get("consensus", "Unknown Consensus"),
                "status": "evidence_collected_from_cache"
            }
        
    queries = state.get("queries", [state["question"]])
    
    # Collect raw evidence
    raw_results = search_tavily(queries)
    if not raw_results:
        return {
            "evidence": [],
            "consensus": "Insufficient Evidence",
            "status": "evidence_collected"
        }
        
    # Prepare LLM extraction
    # Summarize results into a prompt
    docs_text = "\n\n---\n\n".join(
        f"URL: {r['url']}\nTITLE: {r['title']}\nCONTENT:\n{r['content'][:1500]}"
        for r in raw_results
    )
    
    prompt = f"""You are an elite research analyst. Read the following search results and extract the most critical technical claims that answer the user's question.
    
Question: {state["question"]}

Search Results:
{docs_text}

Extract up to 5 key claims. For each claim, provide the source title, URL, the claim itself, and assign a trust_score (0.0 to 1.0).
Rules for trust_score:
- Official docs get 0.9 - 1.0
- High quality community (Reddit/HN/StackOverflow) get 0.6 - 0.8
- Conflicting evidence lowers trust.

Also summarize the overall consensus in a few words (e.g. "Strong Consensus", "Conflicting Evidence", "Weak Consensus").

Return ONLY a JSON object with this exact schema:
{{
    "evidence": [
        {{
            "title": "Document title",
            "url": "https://...",
            "claim": "Specific technical claim...",
            "trust_score": 0.85
        }}
    ],
    "consensus": "Strong Consensus"
}}"""

    try:
        response = _client.chat.completions.create(
            model=_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=1500
        )
        content = json.loads(response.choices[0].message.content)
        evidence = content.get("evidence", [])
        consensus = content.get("consensus", "Unknown Consensus")
    except Exception as e:
        print(f"Error extracting claims: {e}")
        evidence = []
        consensus = "Error Processing Evidence"
        
    # Save to cache
    if slug:
        set_cached_evidence(slug, {"evidence": evidence, "consensus": consensus})
        
    return {
        "evidence": evidence,
        "consensus": consensus,
        "status": "evidence_collected"
    }
