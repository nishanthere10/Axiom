import difflib
from agents.state.comparison_state import ComparisonState

def unified_diff(text_a: str, text_b: str, title: str) -> str:
    """Generate a clean unified diff string."""
    a_lines = text_a.splitlines(keepends=True)
    b_lines = text_b.splitlines(keepends=True)
    
    diff = list(difflib.unified_diff(
        a_lines, b_lines, 
        fromfile=f"Session A ({title})", 
        tofile=f"Session B ({title})", 
        n=2
    ))
    
    if not diff:
        return "No changes."
        
    return "".join(diff)

def generate_structural_diff(state: ComparisonState) -> dict:
    """
    Node 3: Deterministic diffing. No LLM.
    """
    norm_a = state["normalized_a"]
    norm_b = state["normalized_b"]
    
    structural_diff = {
        "recommendation": unified_diff(norm_a["recommendation"], norm_b["recommendation"], "Recommendation"),
        "tradeoffs": unified_diff(norm_a["tradeoffs"], norm_b["tradeoffs"], "Tradeoffs"),
        "alternatives": unified_diff(norm_a["alternatives"], norm_b["alternatives"], "Alternatives"),
        "confidence": unified_diff(norm_a["confidence"], norm_b["confidence"], "Confidence")
    }

    return {
        "structural_diff": structural_diff,
        "status": "diff_generated"
    }
