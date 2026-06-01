from typing import Dict, Any, List
import uuid
from litellm import completion
from api.schemas.memory import MemoryItemCreate
from core.config import settings

def create_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes the completed research and generates compact, retrieval-optimized memory summaries.
    This runs asynchronously outside the main LangGraph to save latency.
    """
    question = state.get("question", "")
    decision = state.get("recommendation", "")
    visuals = state.get("visuals", [])
    
    if not decision:
        return {"new_memories": []}
        
    prompt = f"""
    You are an expert technical architect compressing a recent architectural decision into a retrieval-optimized memory summary.
    This summary will be embedded in a vector database to help inform future architectural decisions.
    
    ORIGINAL QUESTION: {question}
    DECISION/RECOMMENDATION: {decision}
    
    Task: Write a dense, concise summary of this decision. Do not use filler words. Focus purely on technical constraints, chosen technologies, and the definitive stance taken. Maximum 3 sentences.
    """
    
    try:
        response = completion(
            model=settings.LLM_MODEL,
            messages=[{"role": "system", "content": prompt}]
        )
        summary = response.choices[0].message.content.strip()
        
        # Create a MemoryItemCreate object for the decision
        memories = []
        source_id = f"sess_{uuid.uuid4().hex[:8]}" # Placeholder for session id
        
        decision_memory = MemoryItemCreate(
            memory_type="decision",
            source_id=source_id, # Real session_id should be injected if available
            source_type="session",
            summary=summary,
            metadata={
                "question": question,
                "summary": summary,
                "memory_type": "decision"
            },
            scope="temporary"
        )
        memories.append(decision_memory)
        
        # Optionally create preference memory if strong preferences were shown
        # Keeping it simple for V1: just store the decision memory
        
        return {"new_memories": memories}
        
    except Exception as e:
        print(f"Error creating memory summary: {e}")
        return {"new_memories": []}
