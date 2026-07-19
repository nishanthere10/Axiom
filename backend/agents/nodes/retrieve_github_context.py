import logging
from typing import Dict, Any
from agents.state.research_state import ResearchState
from services.context_providers.github_provider import github_provider

logger = logging.getLogger(__name__)

def _get_architecture_summaries(user_id: str) -> list[dict]:
    """Fetches architecture summaries for the user's active repositories."""
    try:
        from services.db import get_supabase
        supabase = get_supabase()
        res = supabase.table("github_repositories").select(
            "repository_name, repository_owner, github_repository_profiles(architecture_summary, tech_stack)"
        ).eq("user_id", user_id).eq("is_active", True).execute()
        
        summaries = []
        for repo in (res.data or []):
            profiles = repo.get("github_repository_profiles", [])
            if profiles and profiles[0].get("architecture_summary"):
                summaries.append({
                    "repository": f"{repo['repository_owner']}/{repo['repository_name']}",
                    "architecture_summary": profiles[0]["architecture_summary"],
                    "tech_stack": profiles[0].get("tech_stack", []),
                })
        return summaries
    except Exception as e:
        logger.warning("Failed to fetch architecture summaries: %s", e)
        return []

def retrieve_github_context(state: ResearchState) -> Dict[str, Any]:
    """
    LangGraph Node: Fetches GitHub repository context relevant to the user's query.
    Executes in parallel with retrieve_memory and decompose_question.
    """
    logger.debug("Retrieving GitHub context for query: %s", state.get("question"))
    
    question = state.get("question", "")
    user_id = state.get("user_id", "anonymous")
    sub_questions = state.get("sub_questions", [])
    
    if sub_questions:
        search_query = question + " " + " ".join(sub_questions[:3])
    else:
        search_query = question

    logger.debug("Retrieving targeted GitHub context for: %s...", search_query[:80])
    
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            chunks = loop.run_until_complete(asyncio.wait_for(
                github_provider.retrieve(
                    query=search_query,
                    user_id=user_id,
                    workspace_id=state.get("workspace_id")
                ),
                timeout=15
            ))
        finally:
            loop.close()
            
        # Inject high-level architecture context alongside raw chunks
        arch_summaries = _get_architecture_summaries(user_id)
        if arch_summaries:
            for summary in arch_summaries:
                chunks.insert(0, {
                    "repository": summary["repository"],
                    "file_path": "__architecture_summary__",
                    "content": summary["architecture_summary"],
                    "raw_snippet": "",
                    "score": 1.0,  # Architecture context is always maximally relevant
                })

        logger.debug(f"Retrieved {len(chunks)} GitHub context chunks.")
        return {"github_context": chunks}
    except Exception as e:
        logger.warning(f"Failed to retrieve GitHub context: {e}")
        return {"github_context": []}
