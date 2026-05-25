from agents.state.comparison_state import ComparisonState

def normalize_documents(state: ComparisonState) -> dict:
    """
    Node 2: Convert both documents into a normalized dictionary for structural diffing.
    No LLM generation, deterministic formatting only.
    """
    doc_a = state["document_a"]
    doc_b = state["document_b"]
    
    def extract(doc):
        # We handle confidence as a single string block or JSON for easy string diffing
        conf = doc.get("confidence", {})
        conf_str = (
            f"Evidence Coverage: {conf.get('evidence_coverage', 0)}\n"
            f"Source Quality: {conf.get('source_quality', 0)}\n"
            f"Contradiction Risk: {conf.get('contradiction_risk', 0)}\n"
            f"Decision Confidence: {conf.get('decision_confidence', 0)}"
        )
        return {
            "recommendation": doc.get("recommendation_context", ""),
            "tradeoffs": doc.get("tradeoffs", ""),
            "alternatives": doc.get("alternatives", ""),
            "confidence": conf_str
        }

    return {
        "normalized_a": extract(doc_a),
        "normalized_b": extract(doc_b),
        "status": "normalized"
    }
