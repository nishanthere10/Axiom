from agents.state.research_state import ResearchState


def format_document(state: ResearchState) -> dict:
    """
    Node 4: Validates all fields are present and marks the pipeline as complete.
    The background task will extract the final state to assemble the DecisionDocument.
    """
    # Ensure critical fields exist (allow empty strings/dicts — they may be valid)
    required_fields = ["question", "recommendation"]
    for field in required_fields:
        if state.get(field) is None:
            raise ValueError(f"Missing required field in research state: {field}")

    # Warn on empty optional fields but don't crash
    optional_fields = ["summary", "tradeoffs", "alternatives", "confidence"]
    for field in optional_fields:
        if not state.get(field):
            import logging
            logging.getLogger(__name__).warning("format_document: field '%s' is empty", field)

    return {"status": "complete"}
