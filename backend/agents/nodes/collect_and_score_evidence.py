import json
import logging
from typing import Dict, Any
from agents.state.research_state import ResearchState
from services.search_provider import search_tavily
from services.evidence_service import get_cached_evidence, set_cached_evidence
from services.llm_provider import generate_chat_completion
from utils.text_optimizer import extract_high_signal_chunks

logger = logging.getLogger(__name__)


def collect_and_score_evidence(state: ResearchState) -> dict:
    """
    Node: Fetches search results and uses LLM to extract and score claims.
    Uses cache if available unless force_refresh logic dictates otherwise.
    Non-critical node — keeps graceful degradation.
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
        f"URL: {r['url']}\nTITLE: {r['title']}\nCONTENT:\n{extract_high_signal_chunks(r.get('content', ''), state['question'], 2500)}"
        for r in raw_results
    )
    
    prompt = f"""You are an elite research analyst. Read the following search results and extract ALL critical technical claims, specifications, edge-cases, and constraints that answer the user's question.
    
Question: {state["question"]}

Search Results:
{docs_text}

Extract the key claims. You must aggressively identify CONTRADICTIONS between sources (e.g. Source A says X, but Source B says Y). If you find contradictions, extract them as claims and heavily penalize their trust_score to highlight the risk.
For each claim, provide the source title, URL, the claim itself, and assign a trust_score (0.0 to 1.0).
Rules for trust_score:
- Official docs get 0.9 - 1.0
- High quality community (Reddit/HN/StackOverflow) get 0.6 - 0.8
- Contradicted claims or outdated information must receive < 0.5.

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
        response = generate_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=4000
        )
        content = json.loads(response.choices[0].message.content)
        evidence = content.get("evidence", [])
        consensus = content.get("consensus", "Unknown Consensus")
    except Exception as e:
        logger.warning("Error extracting claims (non-fatal): %s", e)
        evidence = []
        consensus = "Error Processing Evidence"
        
    warnings = state.get("warnings", [])
    if not evidence and slug:
        warnings.append("⚠️ Evidence collection failed — decision is based on general knowledge only.")
        
    # Save to cache ONLY on success — never cache an error state
    if slug and evidence:
        set_cached_evidence(slug, {"evidence": evidence, "consensus": consensus})
        
    return {
        "evidence": evidence,
        "consensus": consensus,
        "warnings": warnings,
        "status": "evidence_collected"
    }
