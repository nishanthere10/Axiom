from fastapi import HTTPException
from services.db import supabase
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
    # Fetch internal decision_documents IDs to satisfy the foreign key constraint
    doc_a = supabase.table("decision_documents").select("id").eq("session_id", session_a).execute()
    doc_b = supabase.table("decision_documents").select("id").eq("session_id", session_b).execute()
    
    if not doc_a.data or not doc_b.data:
        raise HTTPException(status_code=404, detail="One or both decision documents not found.")
        
    internal_id_a = doc_a.data[0]["id"]
    internal_id_b = doc_b.data[0]["id"]

    # Ensure it's not saved by default
    res = supabase.table("comparisons").insert({
        "id": comparison_id,
        "session_a": internal_id_a,
        "session_b": internal_id_b,
        "summary": summary,
        "structural_diff": structural_diff,
        "decision_evolution": decision_evolution,
        "impact_summary": impact_summary,
        "saved": False
    }).execute()
    
    # Return the data, but swap the internal IDs back to the public session IDs
    # so the frontend receives the UUIDs it originally passed in.
    if res.data:
        created = res.data[0]
        created["session_a"] = session_a
        created["session_b"] = session_b
        return created
    return {}

def get_comparison(comparison_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("comparisons").select("*").eq("id", comparison_id).execute()
    return res.data[0] if res.data else None

def save_comparison(comparison_id: str) -> bool:
    res = supabase.table("comparisons").update({"saved": True}).eq("id", comparison_id).execute()
    return bool(res.data)
