from typing import Dict, Any
from services.pinecone_service import search_memories

def retrieve_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieves historical memories related to the current question using Pinecone.
    Short-circuits (returns empty list) if matches are below threshold (0.70).
    """
    print("[DEBUG: Node] -> retrieve_memory starting...")
    question = state.get("question", "")
    
    # If this is a comparison state, construct a pseudo-question for the vector search
    if not question and "session_a_id" in state and "session_b_id" in state:
        question = f"Compare {state['session_a_id']} vs {state['session_b_id']}"
        print(f"[DEBUG: retrieve_memory] Constructed comparison question: '{question}'")
        
    if not question:
        # Fallback if no question or session context is provided
        print("[DEBUG: retrieve_memory] No question found in state, short-circuiting.")
        return {"retrieved_memories": []}
    
    # We use a threshold of 0.70 as specified in the optimization plan
    print("[DEBUG: retrieve_memory] Calling search_memories...")
    memories = search_memories(query=question, top_k=5, threshold=0.70)
    
    print(f"[DEBUG: retrieve_memory] Retrieved {len(memories)} memories. Exiting node.")
    return {"retrieved_memories": memories}
