import logging
from typing import Dict, Any
from api.schemas.memory import MemoryRelevanceResult
from services.llm_provider import get_instructor_client

logger = logging.getLogger(__name__)

def evaluate_memory_relevance(question: str, memory: Dict[str, Any]) -> MemoryRelevanceResult:
    """
    Evaluates whether a retrieved memory is relevant to the current question.
    Falls back to a score of 1.0 if the LLM fails.
    """
    metadata = memory.get("metadata", {})
    summary = metadata.get("summary", "")
    memory_type = metadata.get("memory_type", "unknown")
    memory_id = memory.get("id", "unknown")
    
    client = get_instructor_client()
    
    prompt = f"""
    You are evaluating the relevance of a historical memory to a new user query.
    
    CURRENT QUERY:
    {question}
    
    MEMORY TO EVALUATE:
    Type: {memory_type}
    Content: {summary}
    
    Determine whether this memory meaningfully helps answer the query.
    Consider topical relevance, decision relevance, and user preference relevance.
    Ignore superficial keyword overlap.
    
    Return a relevance_score between 0.0 and 1.0, and your reasoning.
    The memory_id must be exactly: "{memory_id}"
    """
    
    try:
        logger.debug("Evaluating relevance for memory %s...", memory_id)
        response: MemoryRelevanceResult = client.chat.completions.create(
            model="nvidia/nemotron-3-ultra-550b-a55b",
            response_model=MemoryRelevanceResult,
            max_retries=2,
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        
        # Enforce memory_id correctness just in case
        response.memory_id = memory_id
        return response
    except Exception as e:
        logger.warning("Memory Evaluator failed for %s: %s", memory_id, e)
        # Fallback to current behavior
        return MemoryRelevanceResult(
            memory_id=memory_id,
            relevance_score=1.0,
            reasoning="Fallback: Evaluator failed to score."
        )
