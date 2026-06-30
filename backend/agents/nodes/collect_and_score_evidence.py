import json
import logging
from datetime import datetime
from typing import Dict, Any
from agents.state.research_state import ResearchState
from services.search_provider import search_tavily
from services.evidence_service import get_cached_evidence, set_cached_evidence
from services.llm_provider import generate_chat_completion
from utils.text_optimizer import extract_high_signal_chunks

logger = logging.getLogger(__name__)

TRUSTED_DOMAINS = {
    "postgresql.org": 0.95, "docs.mongodb.com": 0.95, "aws.amazon.com": 0.90,
    "engineering.fb.com": 0.90, "netflixtechblog.com": 0.88,
    "stackoverflow.com": 0.72, "reddit.com": 0.65
}

def authority_boost(url: str) -> float:
    for domain, score in TRUSTED_DOMAINS.items():
        if domain in url:
            return score
    return 0.5


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
    
    # Fast path: if queries is explicitly empty, intent routing determined no search is needed
    if isinstance(queries, list) and len(queries) == 0:
        logger.info("Search skipped: generate_queries determined web search is unnecessary.")
        return {
            "evidence": [],
            "consensus": "Internal Project Query (No Web Search)",
            "warnings": state.get("warnings", []),
            "status": "search_skipped"
        }
    
    # Collect raw evidence
    raw_results = search_tavily(queries)
    if not raw_results:
        return {
            "evidence": [],
            "consensus": "Insufficient Evidence",
            "status": "evidence_collected"
        }
        
    # Token budget: cap each source at 1500 chars and total docs at 28,000 chars (~7k tokens).
    # With 5 taxonomy queries, Tavily can return 5+ results each — uncapped this hits 20k+ tokens.
    MAX_CHARS_PER_SOURCE = 1500
    MAX_TOTAL_CHARS = 28_000

    truncated_parts = []
    total_chars = 0
    for r in raw_results:
        snippet = extract_high_signal_chunks(r.get('content', ''), state['question'], MAX_CHARS_PER_SOURCE)
        part = f"URL: {r['url']}\nTITLE: {r['title']}\nCONTENT:\n{snippet}"
        if total_chars + len(part) > MAX_TOTAL_CHARS:
            break  # Hard stop — never exceed the budget
        truncated_parts.append(part)
        total_chars += len(part)

    docs_text = "\n\n---\n\n".join(truncated_parts)
    
    prompt = f"""You are an elite research analyst. Read the following search results and extract ALL critical technical claims, specifications, edge-cases, and constraints that answer the user's question.
    
Question: {state["question"]}

Search Results:
{docs_text}

Extract the key claims. You must aggressively identify CONTRADICTIONS between sources. If you find contradictions, extract them as claims and heavily penalize their trust_score to highlight the risk.

For each claim, provide:
- "title": source title
- "url": source URL  
- "claim": The specific technical claim (include numbers/metrics when present)
- "claim_type": one of: "benchmark", "tradeoff", "failure_mode", "recommendation", "constraint"
- "metrics": any quantitative data found as a string (e.g. "writes_per_sec: 50k, latency_p99: 12ms") or null
- "trust_score": 0.0 to 1.0. (Official docs: 0.9-1.0, High quality community: 0.6-0.8, Contradicted/outdated: <0.5)
- "source_year": integer year of the article/doc if detectable, else null

Also summarize the overall consensus in a few words (e.g. "Strong Consensus", "Conflicting Evidence", "Weak Consensus").

Return ONLY a JSON object with this exact schema:
{{
    "evidence": [
        {{
            "title": "Document title",
            "url": "https://...",
            "claim": "Specific technical claim...",
            "claim_type": "benchmark",
            "metrics": "latency: 12ms",
            "trust_score": 0.85,
            "source_year": 2024
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
        raw_evidence = content.get("evidence", [])
        consensus = content.get("consensus", "Unknown Consensus")
        
        current_year = datetime.now().year
        
        evidence = []
        for e in raw_evidence:
            # Boost score based on authority
            llm_score = float(e.get("trust_score", 0.5))
            url = e.get("url", "")
            final_score = 0.6 * llm_score + 0.4 * authority_boost(url)
            e["trust_score"] = min(1.0, max(0.0, final_score))
            
            # Filter stale evidence (> 5 years old)
            source_year_val = e.get("source_year")
            if source_year_val is None:
                evidence.append(e)
            else:
                try:
                    parsed_year = int(float(str(source_year_val).replace(',', '')))
                    if (current_year - parsed_year) <= 5:
                        evidence.append(e)
                except (ValueError, TypeError):
                    # If we can't parse it, err on the side of keeping it
                    evidence.append(e)
                
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
