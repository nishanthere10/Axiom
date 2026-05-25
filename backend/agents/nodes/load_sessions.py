from agents.state.comparison_state import ComparisonState
from services import research_service

def load_sessions(state: ComparisonState) -> dict:
    """
    Node 1: Load both decision documents from the database.
    """
    session_a = state["session_a_id"]
    session_b = state["session_b_id"]
    
    doc_a = research_service.get_document_by_session(session_a)
    doc_b = research_service.get_document_by_session(session_b)
    
    if not doc_a or not doc_b:
        raise ValueError("One or both sessions could not be found.")
        
    return {
        "document_a": doc_a,
        "document_b": doc_b,
        "status": "sessions_loaded"
    }
