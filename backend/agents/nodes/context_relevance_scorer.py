"""
LangGraph Node: Context Relevance Scorer

Runs AFTER retrieve_memory, retrieve_github_context, and analyze_memory.
Runs BEFORE generate_decision.

Scores every retrieved memory and GitHub chunk against the decomposed question intent.
Only context above RELEVANCE_THRESHOLD is passed to generate_decision.

Scoring strategy:
- Uses a lightweight LLM call (fast/cheap model) to score each candidate 0.0–1.0
- Falls back to embedding cosine similarity if LLM call fails
- Hard cap: at most MAX_MEMORIES memories and MAX_GITHUB_CHUNKS GitHub chunks pass through
"""
import logging
import json
from typing import Dict, Any, List
from agents.state.research_state import ResearchState
from services.llm_provider import generate_chat_completion

logger = logging.getLogger(__name__)

RELEVANCE_THRESHOLD = 0.65
MAX_MEMORIES       = 4    # hard cap even above threshold
MAX_GITHUB_CHUNKS  = 6    # hard cap even above threshold


def _score_candidates_with_llm(
    intent: str,
    sub_questions: list[str],
    candidates: list[dict],
    content_key: str,
) -> list[dict]:
    """
    Sends all candidates to a single lightweight LLM call.
    Returns same list with 'relevance_score' (float 0.0–1.0) added to each.
    Single call handles all candidates — not N calls.
    """
    if not candidates:
        return []

    # Build the scoring prompt
    intent_block = f"Question: {intent}"
    if sub_questions:
        intent_block += "\nSub-questions:\n" + "\n".join(f"- {q}" for q in sub_questions[:5])

    candidates_block = "\n\n".join(
        f"[{i}] {c.get(content_key, c.get('content', c.get('summary', '')))[:300]}"
        for i, c in enumerate(candidates)
    )

    prompt = f"""You are a relevance scorer for an AI research assistant.

RESEARCH INTENT:
{intent_block}

CONTEXT CANDIDATES TO SCORE:
{candidates_block}

Score each candidate's relevance to the research intent from 0.0 (irrelevant) to 1.0 (highly relevant).
Respond ONLY with a JSON array of numbers, one per candidate, in order.
Example for 3 candidates: [0.9, 0.2, 0.75]
Do not explain. Only output the JSON array."""

    try:
        messages = [{"role": "user", "content": prompt}]
        response = generate_chat_completion(
            messages,
            model="groq/llama-3.3-70b-versatile",   # lightweight/fast scoring model
            max_tokens=100,
            temperature=0.0,
        )
        raw = response.choices[0].message.content.strip()
        # Handle cases where the LLM might wrap the JSON array in markdown code blocks
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        scores = json.loads(raw)
        if not isinstance(scores, list) or len(scores) != len(candidates):
            raise ValueError("Score count mismatch")
        for i, c in enumerate(candidates):
            c["relevance_score"] = float(max(0.0, min(1.0, scores[i])))
        return candidates
    except Exception as e:
        logger.warning("LLM relevance scoring failed (%s) — falling back to 1.0", e)
        # Fallback: pass all candidates through at full score
        for c in candidates:
            c["relevance_score"] = 1.0
        return candidates


def context_relevance_scorer(state: ResearchState) -> Dict[str, Any]:
    """
    LangGraph Node: Scores and filters retrieved context before generation.
    """
    question = state.get("question", "")
    sub_questions = state.get("sub_questions", [])
    retrieved_memories = state.get("retrieved_memories", [])
    github_context = state.get("github_context", [])

    logger.debug(
        "context_relevance_scorer: scoring %d memories, %d github chunks",
        len(retrieved_memories), len(github_context)
    )

    # Score memories
    scored_memories = _score_candidates_with_llm(
        intent=question,
        sub_questions=sub_questions,
        candidates=[dict(m) for m in retrieved_memories],
        content_key="summary",
    )

    # Score GitHub chunks
    scored_github = _score_candidates_with_llm(
        intent=question,
        sub_questions=sub_questions,
        candidates=[dict(g) for g in github_context],
        content_key="content",
    )

    # Filter by threshold and cap
    passing_memories = sorted(
        [m for m in scored_memories if m.get("relevance_score", 0) >= RELEVANCE_THRESHOLD],
        key=lambda m: m.get("relevance_score", 0),
        reverse=True,
    )[:MAX_MEMORIES]

    passing_github = sorted(
        [g for g in scored_github if g.get("relevance_score", 0) >= RELEVANCE_THRESHOLD],
        key=lambda g: g.get("relevance_score", 0),
        reverse=True,
    )[:MAX_GITHUB_CHUNKS]

    total_candidates = len(scored_memories) + len(scored_github)
    total_passing    = len(passing_memories) + len(passing_github)
    dropped          = total_candidates - total_passing

    logger.info(
        "context_relevance_scorer: %d/%d candidates pass threshold %.2f "
        "(memories: %d/%d, github: %d/%d, dropped: %d)",
        total_passing, total_candidates, RELEVANCE_THRESHOLD,
        len(passing_memories), len(scored_memories),
        len(passing_github), len(scored_github),
        dropped,
    )

    return {
        "scored_memories":       passing_memories,    # filtered, sorted
        "scored_github":         passing_github,       # filtered, sorted
        "injected_memory_count": len(passing_memories),
        "injected_github_count": len(passing_github),
        "dropped_context_count": dropped,
        "status":                "scoring context",
    }
