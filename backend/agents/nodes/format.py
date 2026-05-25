from agents.state.research_state import ResearchState


def format_document(state: ResearchState) -> dict:
    """
    Node 4: Validates all fields are present and marks the pipeline as complete.
    The background task will extract the final state to assemble the DecisionDocument.
    """
    # Ensure all required fields exist and are non-empty
    required_fields = ["question", "summary", "recommendation", "tradeoffs", "alternatives", "confidence"]
    for field in required_fields:
        if not state.get(field):
            raise ValueError(f"Missing required field in research state: {field}")

    return {"status": "complete"}
