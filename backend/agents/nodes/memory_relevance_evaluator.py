import logging
from typing import Dict, Any
import concurrent.futures
from services.memory_relevance_service import evaluate_memory_relevance

logger = logging.getLogger(__name__)

def memory_relevance_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates the relevance of retrieved memories, ranks them, and filters out highly irrelevant ones.
    Pinned memories automatically pass with a score of 1.0.
    """
    logger.debug("Node -> memory_relevance_evaluator starting...")
    memories = state.get("retrieved_memories", [])
    
    if not memories:
        logger.debug("No memories to evaluate.")
        return {"retrieved_memories": []}
        
    question = state.get("question", "")
    if not question and "session_a_id" in state and "session_b_id" in state:
        question = f"Compare {state['session_a_id']} vs {state['session_b_id']}"
        
    if not question:
        return {"retrieved_memories": memories}

    evaluated_memories = []
    memories_to_evaluate = []

    # Stage 1: Rule-Based Filter (Pinned Memories)
    for memory in memories:
        if "metadata" not in memory:
            memory["metadata"] = {}
            
        metadata = memory["metadata"]
        # If the memory is explicitly pinned, bypass evaluation
        if metadata.get("pinned", False) or metadata.get("is_pinned", False):
            logger.debug("Memory %s is pinned. Bypassing evaluation.", memory.get("id"))
            memory["metadata"]["relevance_score"] = 1.0
            memory["metadata"]["relevance_reasoning"] = "Pinned by user"
            evaluated_memories.append(memory)
        else:
            memories_to_evaluate.append(memory)

    # Stage 2: LLM Evaluation
    if memories_to_evaluate:
        logger.debug("Evaluating %d memories concurrently...", len(memories_to_evaluate))
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_memory = {
                executor.submit(evaluate_memory_relevance, question, m): m 
                for m in memories_to_evaluate
            }
            
            for future in concurrent.futures.as_completed(future_to_memory):
                m = future_to_memory[future]
                if "metadata" not in m:
                    m["metadata"] = {}
                    
                try:
                    result = future.result()
                    m["metadata"]["relevance_score"] = result.relevance_score
                    m["metadata"]["relevance_reasoning"] = result.reasoning
                    
                    # Filter out memories with very low relevance (e.g. < 0.3)
                    if result.relevance_score >= 0.3:
                        evaluated_memories.append(m)
                    else:
                        logger.debug("Filtered out memory %s with low relevance: %.2f", m.get("id"), result.relevance_score)
                except Exception as e:
                    logger.warning("Failed to evaluate memory %s: %s", m.get("id"), e)
                    # Fallback
                    m["metadata"]["relevance_score"] = 1.0
                    m["metadata"]["relevance_reasoning"] = "Fallback: Evaluator failed."
                    evaluated_memories.append(m)

    # Rank memories by relevance_score descending
    evaluated_memories.sort(key=lambda x: x.get("metadata", {}).get("relevance_score", 0.0), reverse=True)
    
    return {"retrieved_memories": evaluated_memories}
