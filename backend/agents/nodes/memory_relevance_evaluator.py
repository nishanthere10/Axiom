import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def memory_relevance_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Rule-based pre-filter for memories. Pinned memories get score 1.0.
    LLM-based relevance scoring is handled downstream by context_relevance_scorer.
    """
    logger.debug("Node -> memory_relevance_evaluator starting...")
    memories = state.get("retrieved_memories", [])
    
    if not memories:
        logger.debug("No memories to evaluate.")
        return {"retrieved_memories": []}
        
    # Tag pinned memories with score 1.0; pass all others through for downstream LLM scoring
    for memory in memories:
        if "metadata" not in memory:
            memory["metadata"] = {}
        metadata = memory["metadata"]
        if metadata.get("pinned", False) or metadata.get("is_pinned", False):
            memory["metadata"]["relevance_score"] = 1.0
            memory["metadata"]["relevance_reasoning"] = "Pinned by user"

    return {"retrieved_memories": memories}
