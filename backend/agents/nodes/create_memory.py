from typing import Dict, Any, List
import uuid
from api.schemas.memory import MemoryItemCreate
from core.config import settings
from services.llm_provider import generate_chat_completion

def create_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes the completed research and generates compact, retrieval-optimized memory summaries.
    This runs asynchronously outside the main LangGraph to save latency.
    """
    print("[DEBUG: Node] -> create_memory starting...")
    is_comparison = "session_a_id" in state and "session_b_id" in state
    
    if is_comparison:
        print("[DEBUG: create_memory] Detected comparison state.")
        return _create_comparison_memory(state)
    else:
        print("[DEBUG: create_memory] Detected research state.")
        return _create_decision_memory(state)

def _create_decision_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    question = state.get("question", "")
    decision = state.get("recommendation", "")
    
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
        response = generate_chat_completion(
            model="groq/llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": prompt}]
        )
        summary = response.choices[0].message.content.strip()
        
        memories = []
        session_id = state.get("session_id")
        source_id = session_id if session_id else f"sess_{uuid.uuid4().hex[:8]}"
        
        decision_memory = MemoryItemCreate(
            memory_type="decision",
            source_id=source_id,
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
        return {"new_memories": memories}
        
    except Exception as e:
        print(f"Error creating decision memory: {e}")
        return {"new_memories": []}

def _create_comparison_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    session_a = state.get("session_a_id", "A")
    session_b = state.get("session_b_id", "B")
    impact_summary = state.get("impact_summary", {})
    structural_diff = state.get("structural_diff", {})
    
    if not impact_summary:
        return {"new_memories": []}
        
    prompt = f"""
    You are an expert technical architect summarizing a recent architectural comparison between {session_a} and {session_b}.
    This summary will be embedded in a vector database to help inform future architectural decisions.
    
    IMPACT SUMMARY: {impact_summary}
    STRUCTURAL DIFF: {structural_diff}
    
    Task: Write a dense, concise summary of this comparison. Focus purely on the trade-offs evaluated and the key outcome or preference established between the two approaches. Maximum 3 sentences.
    """
    
    try:
        response = generate_chat_completion(
            model="groq/llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": prompt}]
        )
        summary = response.choices[0].message.content.strip()
        
        memories = []
        comparison_id = state.get("comparison_id", f"comp_{uuid.uuid4().hex[:8]}")
        
        comp_memory = MemoryItemCreate(
            memory_type="comparison",
            source_id=comparison_id,
            source_type="comparison",
            summary=summary,
            metadata={
                "session_a": session_a,
                "session_b": session_b,
                "summary": summary,
                "memory_type": "comparison"
            },
            scope="temporary"
        )
        memories.append(comp_memory)
        return {"new_memories": memories}
        
    except Exception as e:
        print(f"Error creating comparison memory: {e}")
        return {"new_memories": []}
