import logging
from typing import Dict, Any
from agents.state.research_state import ResearchState
from services.context_providers.github_provider import github_provider

logger = logging.getLogger(__name__)

def retrieve_github_context(state: ResearchState) -> Dict[str, Any]:
    """
    LangGraph Node: Fetches GitHub repository context relevant to the user's query.
    Executes in parallel with retrieve_memory and decompose_question.
    """
    logger.debug("Retrieving GitHub context for query: %s", state.get("question"))
    
    question = state.get("question", "")
    user_id = state.get("user_id", "anonymous")
    
    import asyncio
    try:
        # Use a new event loop or the existing one depending on how LangGraph invokes it
        try:
            loop = asyncio.get_running_loop()
            chunks = loop.run_until_complete(github_provider.retrieve(question, user_id))
        except RuntimeError:
            chunks = asyncio.run(github_provider.retrieve(question, user_id))
            
        logger.debug(f"Retrieved {len(chunks)} GitHub context chunks.")
        return {"github_context": chunks}
    except Exception as e:
        logger.warning(f"Failed to retrieve GitHub context: {e}")
        return {"github_context": []}
