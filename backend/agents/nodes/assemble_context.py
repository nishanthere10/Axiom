import logging
from typing import Dict, Any
from agents.state.research_state import ResearchState
from agents.domain.engineered_context import EngineeredContext

logger = logging.getLogger(__name__)

def assemble_context(state: ResearchState) -> Dict[str, Any]:
    """
    LangGraph Node: Single Context Assembly Path.
    Evaluates candidate knowledge (memories, repo code, external evidence)
    and constructs a deterministic, unified EngineeredContext object.
    """
    evidence = state.get("evidence", [])
    memories = state.get("scored_memories") or state.get("retrieved_memories", [])
    github_context = state.get("scored_github") or state.get("github_context", [])
    memory_context = state.get("memory_context", {})

    injected_mem = state.get("injected_memory_count", len(memories))
    injected_git = state.get("injected_github_count", len(github_context))
    dropped = state.get("dropped_context_count", 0)

    logger.info(
        "assemble_context: assembling %d memories, %d github chunks (%d dropped by relevance gate)",
        injected_mem, injected_git, dropped
    )

    # 1. Format memory context
    preferences = memory_context.get("preferences", [])
    historical_patterns = memory_context.get("historical_patterns", [])
    related_decisions = memory_context.get("related_decisions", [])
    consistency_warnings = memory_context.get("consistency_warnings", [])

    memory_text = ""
    if preferences:
        memory_text += "\n**USER PREFERENCES (from memory):**\n" + "\n".join(
            f"- {p.get('value', '')}: {p.get('reason', '')}"
            for p in preferences
            if isinstance(p, dict)
        )
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

    # 2. Format evidence context
    evidence_text = "\n\n".join(
        f"[Source {i+1}] ({e.get('claim_type','unknown').upper()} | trust:{e.get('trust_score',0):.2f} | {e.get('source_year','?')})\n"
        f"  Title: {e.get('title')}\n"
        f"  Claim: {e.get('claim')}\n"
        f"  Metrics: {e.get('metrics') or 'none'}\n"
        f"  URL: {e.get('url')}"
        for i, e in enumerate(sorted(evidence, key=lambda x: x.get('trust_score', 0), reverse=True))
    )

    # 3. Format repository context (architecture blueprint + code snippets)
    arch_chunks = [c for c in github_context if c.get("file_path") == "__architecture_summary__"]
    code_chunks = [c for c in github_context if c.get("file_path") != "__architecture_summary__"]

    github_text_parts = []
    if arch_chunks:
        github_text_parts.append("**REPOSITORY ARCHITECTURE & TECH STACK BLUEPRINT:**")
        for arch in arch_chunks:
            # FIX: Handle tech_stack as either dict or string
            tech_stack_data = arch.get("tech_stack", [])
            
            # Safely join, extracting the string if it's a dictionary, or just keeping it if it's already a string
            tech_stack = ", ".join(
                [item.get("name", str(item)) if isinstance(item, dict) else str(item) for item in tech_stack_data]
            ) if tech_stack_data else ""
            
            stack_str = f" (Tech Stack: {tech_stack})" if tech_stack else ""
            github_text_parts.append(f"Repo: {arch.get('repository')}{stack_str}\n{arch.get('content')}")

    if code_chunks:
        github_text_parts.append("**REPOSITORY CODE & DOCUMENTATION SNIPPETS:**")
        for chunk in code_chunks:
            github_text_parts.append(
                f"[Source: {chunk.get('file_path', 'unknown')} | {chunk.get('repository', 'unknown')}]\n"
                f"{chunk.get('raw_snippet') or chunk.get('content', '')}"
            )

    github_text = "\n\n".join(github_text_parts)

    context_obj = EngineeredContext(
        memory_text=memory_text,
        evidence_text=evidence_text,
        github_text=github_text,
        warnings=[str(w) for w in consistency_warnings],
        sources=[{"title": e.get("title"), "url": e.get("url")} for e in evidence if e.get("url")]
    )

    return {"engineered_context": context_obj.model_dump()}
