import logging
import time
from typing import Dict, Any
from services.pinecone_service import search_memories

logger = logging.getLogger(__name__)


def retrieve_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieves historical memories related to the current question using Pinecone.

    Uses the improved search_memories with:
    - top_k=15: fetches more candidates from Pinecone's ANN index
    - max_results=5: caps the final return after threshold filtering
    - Score-sorted: best matches returned first

    Combined with richer embed_text at upsert time (question + summary + constraints),
    this achieves significantly better recall without adding any extra API calls.
    """
    logger.debug("Node -> retrieve_memory starting...")
    question = state.get("question", "")

    # For comparison states, construct a pseudo-question for vector search
    if not question and "session_a_id" in state and "session_b_id" in state:
        question = f"Compare {state['session_a_id']} vs {state['session_b_id']}"
        logger.debug("Constructed comparison question: '%s'", question)

    if not question:
        logger.debug("No question found in state, short-circuiting.")
        return {"retrieved_memories": []}

    user_id = state.get("user_id", "anonymous")
    workspace_id = state.get("workspace_id")

    start_time = time.time()

    # Single Pinecone call with wider net (top_k=15) and best-first ordering
    memories = search_memories(
        query=question,
        user_id=user_id,
        workspace_id=workspace_id,
        top_k=15,
        threshold=0.70,
        max_results=5,
    )

    latency_ms = int((time.time() - start_time) * 1000)
    logger.debug("retrieve_memory: %d memories in %dms", len(memories), latency_ms)

    try:
        from services.metrics_service import emit_memory_retrieved
        emit_memory_retrieved(
            user_id=user_id,
            retrieved_count=len(memories),
            used_count=len(memories),
            latency_ms=latency_ms,
            hit=len(memories) > 0
        )
    except Exception as e:
        logger.warning("Failed to emit memory metrics: %s", e)

    return {"retrieved_memories": memories}
