from services.db import db
from typing import Dict, Any, Optional

def create_comparison(
    comparison_id: str,
    session_a: str,
    session_b: str,
    summary: str,
    structural_diff: Dict[str, Any],
    decision_evolution: str,
    impact_summary: str
) -> Dict[str, Any]:
    # Ensure it's not saved by default
    res = db.table("comparisons").insert({
        "id": comparison_id,
        "session_a": session_a,
        "session_b": session_b,
        "summary": summary,
        "structural_diff": structural_diff,
        "decision_evolution": decision_evolution,
        "impact_summary": impact_summary,
        "saved": False
    }).execute()
    return res.data[0] if res.data else {}

def get_comparison(comparison_id: str) -> Optional[Dict[str, Any]]:
    res = db.table("comparisons").select("*").eq("id", comparison_id).execute()
    return res.data[0] if res.data else None

def save_comparison(comparison_id: str) -> bool:
    res = db.table("comparisons").update({"saved": True}).eq("id", comparison_id).execute()
    return bool(res.data)
