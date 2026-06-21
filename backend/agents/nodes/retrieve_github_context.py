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
    import concurrent.futures
    try:
        # FastAPI/LangGraph runs in an existing event loop. 
        # asyncio.run() or loop.run_until_complete() will crash if called from within a running loop.
        # We safely execute the async retrieve method by running it in a new thread.
        def _run_async_retrieve():
            return asyncio.run(github_provider.retrieve(question, user_id))
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run_async_retrieve)
            chunks = future.result(timeout=15)
            
        logger.debug(f"Retrieved {len(chunks)} GitHub context chunks.")
        return {"github_context": chunks}
    except Exception as e:
        logger.warning(f"Failed to retrieve GitHub context: {e}")
        return {"github_context": []}
