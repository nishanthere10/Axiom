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
    constraints = state.get("constraints", [])
    
    constraints_text = "\n".join(f"- {c}" for c in constraints) if constraints else "None detected."
    
    prompt = f"""You are a technical research engineer evaluating query intent and generating search queries.

QUESTION: {question}
ARCHITECTURAL BRIEF: {summary}
HARD CONSTRAINTS DETECTED: 
{constraints_text}

Task 1: Determine if this question requires external web research (e.g. asking about specific technology benchmarks, external tools, architectures) OR if it is a purely internal project question (e.g. "What should we do next on the Fitmart Project?", "How does our current system work?").

Task 2: IF the question requires web research, generate 5 highly targeted search queries across these CATEGORIES (exactly one per category):
1. BENCHMARK: Find performance benchmarks, latency numbers, throughput data.
2. TRADEOFF: Find architectural trade-off analyses and case studies.
3. FAILURE MODE: Find known failure modes, outage reports, gotchas.
4. CONSENSUS: Find what engineers with this exact use-case chose and why.
5. ALTERNATIVE: Find the best rejected alternative.

IF the question does NOT require web research, return an empty array for queries.

Return ONLY a JSON object with this exact schema:
{{
    "requires_web_search": boolean,
    "queries": ["query 1", "query 2"] // Empty array if requires_web_search is false
}}"""

    try:
        response = generate_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=600
        )
        content = json.loads(response.choices[0].message.content)
        queries = content.get("queries", [])
    except Exception:
        # Failsafe: assume search is needed
        queries = [question]
        
    return {
        "queries": queries,
        "status": "queries_generated"
    }
