from agents.state.comparison_state import ComparisonState

def format_comparison(state: ComparisonState) -> dict:
    """
    Node 6: Validates final state and marks the graph complete.
    """
    if not state.get("structural_diff") or not state.get("decision_evolution"):
        raise ValueError("Comparison pipeline failed to generate required outputs.")
        
    return {
        "status": "complete"
    }
