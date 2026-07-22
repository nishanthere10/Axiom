import json
import logging
from core.config import settings
from agents.state.research_state import ResearchState
from services.llm_provider import async_generate_chat_completion

logger = logging.getLogger(__name__)


async def generate_decision(state: ResearchState) -> dict:
    """
    Node 2: Generates the full engineering decision — recommendation context,
    tradeoffs, and alternatives — using the question and executive summary.
    """
    question = state["question"]
    summary = state["summary"]
    evidence = state.get("evidence", [])
    
    # Use relevance-filtered context if available
    memories = state.get("scored_memories") or state.get("retrieved_memories", [])
    github_context = state.get("scored_github") or state.get("github_context", [])
    memory_context = state.get("memory_context", {})

    injected_mem = state.get("injected_memory_count", len(memories))
    injected_git = state.get("injected_github_count", len(github_context))
    dropped = state.get("dropped_context_count", 0)

    logger.info(
        "generate_decision: injecting %d memories, %d github chunks (%d dropped by relevance gate)",
        injected_mem, injected_git, dropped
    )
    
    eng_ctx = state.get("engineered_context", {})
    if eng_ctx:
        memory_text = eng_ctx.get("memory_text", "No memory context.")
        evidence_text = eng_ctx.get("evidence_text", "No external evidence provided.")
        github_text = eng_ctx.get("github_text", "No repository context provided.")
    else:
        # Extract ALL memory context fields
        preferences = memory_context.get("preferences", [])
        historical_patterns = memory_context.get("historical_patterns", [])
        related_decisions = memory_context.get("related_decisions", [])
        consistency_warnings = memory_context.get("consistency_warnings", [])

        memory_text = ""
        if preferences:
            memory_text += "\n**USER PREFERENCES (from memory):**\n" + "\n".join(f"- {p['value']}: {p['reason']}" for p in preferences)
        if historical_patterns:
            memory_text += "\n**HISTORICAL PATTERNS:**\n" + "\n".join(f"- {h}" for h in historical_patterns)
        if related_decisions:
            memory_text += "\n**RELATED PAST DECISIONS (Summary):**\n" + "\n".join(f"- {d}" for d in related_decisions)
        if consistency_warnings:
            memory_text += "\n**⚠️ CONSISTENCY WARNINGS:**\n" + "\n".join(f"- {w}" for w in consistency_warnings)
            
        if memories:
            memory_text += "\n**RELEVANT PAST DECISIONS (Raw Context):**\n" + "\n".join(
                f"- [{m.get('metadata', {}).get('memory_type', 'unknown')}] {m.get('metadata', {}).get('summary', '')}"
                for m in memories
            )

        # Format evidence for the prompt with rich formatting and sorted by trust_score
        evidence_text = "\n\n".join(
            f"[Source {i+1}] ({e.get('claim_type','unknown').upper()} | trust:{e.get('trust_score',0):.2f} | {e.get('source_year','?')})\n"
            f"  Title: {e.get('title')}\n"
            f"  Claim: {e.get('claim')}\n"
            f"  Metrics: {e.get('metrics') or 'none'}\n"
            f"  URL: {e.get('url')}"
            for i, e in enumerate(sorted(evidence, key=lambda x: x.get('trust_score', 0), reverse=True))
        )

        # Format repository context
        github_text = "\n\n".join(
            f"[Source: {chunk.get('file_path', 'unknown')} | {chunk.get('repository', 'unknown')}]\n{chunk.get('raw_snippet') or chunk.get('content', '')}"
            for chunk in github_context
        )

    prompt = f"""You are a distinguished Principal Software Engineer. Based on the technical question, analysis, and the provided EVIDENCE, MEMORY, and REPOSITORY CONTEXT, generate a highly scannable, expert-level decision document. 
Do not use huge text blocks. Use bullet points and bold text to make it readable at a glance. Prioritize context-rich quality over quantity.

CRITICAL RULES:
1. Your recommendation MUST directly address the user's detected constraints and existing architecture.
2. You MUST reference user preferences from memory when they exist (e.g. "Given your existing use of Redis, consider...")  
3. For every key claim, cite the source: [Source N] or [Source: file_path] — do NOT make uncited claims.
4. If consistency_warnings exist in MEMORY, address them explicitly in your reasoning_scratchpad.
5. Your recommendation MUST include at least one concrete metric (latency, throughput, cost) derived from Evidence if available.
6. Keep each bullet point ≤15 words. No paragraph prose.

Question: {question}

Analysis: {summary}

Memory Context:{memory_text if memory_text else " No memory context."}

Evidence:
{evidence_text if evidence else "No external evidence provided."}

Repository Context:
{github_text if github_context else "No repository context provided."}

Return a JSON object with exactly these keys. The value for each key MUST be a single Markdown string, NOT nested JSON objects or arrays:
- "reasoning_scratchpad": A string where you actively debate the pros and cons, resolve contradictions in the evidence, and weigh tradeoffs mathematically against the repository context and memory context. This is your Chain-of-Thought space to reach the best conclusion. Do this FIRST.
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
    response = await async_generate_chat_completion(
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
