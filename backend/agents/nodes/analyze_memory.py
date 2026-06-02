from typing import Dict, Any
import instructor
from litellm import completion
from api.schemas.memory import MemoryContextSchema
from core.config import settings

def analyze_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes retrieved memories to extract preferences, patterns, and warnings.
    If no memories were retrieved, short-circuits and returns an empty context.
    """
    print("[DEBUG: Node] -> analyze_memory starting...")
    memories = state.get("retrieved_memories", [])
    
    if not memories:
        # Short-circuit logic to save LLM calls if no highly relevant memories were found
        print("[DEBUG: analyze_memory] No highly relevant memories retrieved. Short-circuiting LLM analysis.")
        return {
            "memory_context": {
                "preferences": [],
                "historical_patterns": [],
                "related_decisions": [],
                "consistency_warnings": []
            }
        }
        
    question = state.get("question", "")
    if not question and "session_a_id" in state and "session_b_id" in state:
        question = f"Compare {state['session_a_id']} vs {state['session_b_id']}"
    
    # Format the memories for the LLM prompt
    formatted_memories = []
    for idx, m in enumerate(memories):
        metadata = m.get("metadata", {})
        summary = metadata.get("summary", "")
        mem_type = metadata.get("memory_type", "unknown")
        formatted_memories.append(f"Memory {idx+1} ({mem_type}): {summary}")
        
    memories_text = "\n".join(formatted_memories)
        
    client = instructor.from_litellm(completion)
    
    prompt = f"""
    You are analyzing the user's historical architectural memories to inform a new decision.
    
    CURRENT QUESTION:
    {question}
    
    RETRIEVED MEMORIES:
    {memories_text}
    
    Your task is to analyze these memories and extract:
    1. Any detected technical preferences (e.g. they prefer serverless, they like Postgres).
    2. Historical patterns (e.g. they usually choose open source).
    3. Directly related decisions that inform the current question.
    4. Consistency warnings (e.g. if the user is asking about NoSQL but their history heavily favors relational DBs, flag this).
    
    Be concise and objective.
    """
    
    try:
        print("[DEBUG: analyze_memory] Querying LLM to analyze memory context...")
        response: MemoryContextSchema = client.chat.completions.create(
            model="groq/llama-3.3-70b-versatile",
            response_model=MemoryContextSchema,
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        print("[DEBUG: analyze_memory] Successfully parsed LLM memory context. Exiting node.")
        return {"memory_context": response.model_dump()}
    except Exception as e:
        print(f"[DEBUG: analyze_memory] Memory Analysis Error: {e}")
        # Fallback to empty context on error to not crash pipeline
        return {
            "memory_context": {
                "preferences": [],
                "historical_patterns": [],
                "related_decisions": [],
                "consistency_warnings": []
            }
        }
