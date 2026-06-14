import logging
from typing import Dict, Any
from services.pinecone_service import search_memories

logger = logging.getLogger(__name__)

def retrieve_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieves historical memories related to the current question using Pinecone.
    Short-circuits (returns empty list) if matches are below threshold (0.70).
    """
    logger.debug("Node -> retrieve_memory starting...")
    question = state.get("question", "")
    
    # If this is a comparison state, construct a pseudo-question for the vector search
    if not question and "session_a_id" in state and "session_b_id" in state:
        question = f"Compare {state['session_a_id']} vs {state['session_b_id']}"
        logger.debug("Constructed comparison question: '%s'", question)
        
    if not question:
        # Fallback if no question or session context is provided
        logger.debug("No question found in state, short-circuiting.")
        return {"retrieved_memories": []}
    
    # We use a threshold of 0.70 as specified in the optimization plan
    logger.debug("Calling search_memories...")
    user_id = state.get("user_id", "anonymous")
    
    import time
    start_time = time.time()
    memories = search_memories(query=question, user_id=user_id, top_k=5, threshold=0.70)
    latency_ms = int((time.time() - start_time) * 1000)
    
    try:
        from services.metrics_service import emit_memory_retrieved
        emit_memory_retrieved(
            user_id=user_id,
            retrieved_count=len(memories),
            used_count=len(memories), # Current implementation uses all retrieved memories
            latency_ms=latency_ms,
            hit=len(memories) > 0
        )
    except Exception as e:
        logger.warning(f"Failed to emit memory metrics: {e}")
        
    logger.debug("search_memories returned %d results", len(memories))
    return {"retrieved_memories": memories}
