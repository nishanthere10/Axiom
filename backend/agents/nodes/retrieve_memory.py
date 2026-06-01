from typing import Dict, Any
from services.pinecone_service import search_memories

def retrieve_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieves historical memories related to the current question using Pinecone.
    Short-circuits (returns empty list) if matches are below threshold (0.80).
    """
    question = state.get("question", "")
    
    # If this is a comparison state, construct a pseudo-question for the vector search
    if not question and "session_a_id" in state and "session_b_id" in state:
        question = f"Compare {state['session_a_id']} vs {state['session_b_id']}"
        
    if not question:
        # Fallback if no question or session context is provided
        return {"retrieved_memories": []}
    
    # We use a threshold of 0.80 as specified in the optimization plan
    memories = search_memories(query=question, top_k=5, threshold=0.80)
    
    return {"retrieved_memories": memories}
