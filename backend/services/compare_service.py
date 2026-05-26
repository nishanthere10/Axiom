import json
from fastapi import HTTPException
from services.db import supabase
from typing import Dict, Any, Optional

def create_comparison(
    comparison_id: str,
    session_a: str,
    session_b: str,
    summary: str,
    structural_diff: Dict[str, Any],
    decision_evolution: Dict[str, Any],
    impact_summary: Dict[str, Any]
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
        "decision_evolution": json.dumps(decision_evolution),
        "impact_summary": json.dumps(impact_summary),
        "saved": False
    }).execute()
    
    # Return the data, but swap the internal IDs back to the public session IDs
    # so the frontend receives the UUIDs it originally passed in.
    if res.data:
        created = res.data[0]
        created["session_a"] = session_a
        created["session_b"] = session_b
        try:
            created["decision_evolution"] = json.loads(created["decision_evolution"])
            created["impact_summary"] = json.loads(created["impact_summary"])
        except Exception:
            pass
        return created
    return {}

def get_comparison(comparison_id: str) -> Optional[Dict[str, Any]]:
    res = supabase.table("comparisons").select("*").eq("id", comparison_id).execute()
    if not res.data:
        return None
    comp = res.data[0]
    try:
        comp["decision_evolution"] = json.loads(comp["decision_evolution"])
        comp["impact_summary"] = json.loads(comp["impact_summary"])
    except Exception:
        pass
    return comp

def save_comparison(comparison_id: str) -> bool:
    res = supabase.table("comparisons").update({"saved": True}).eq("id", comparison_id).execute()
    return bool(res.data)

def get_saved_comparisons() -> list[Dict[str, Any]]:
    # We query the comparisons table where saved is True and join with decision_documents to get original session IDs
    res = supabase.table("comparisons") \
        .select("id, summary, created_at, doc_a:decision_documents!session_a(session_id), doc_b:decision_documents!session_b(session_id)") \
        .eq("saved", True) \
        .order("created_at", desc=True) \
        .execute()
    
    if not res.data:
        return []
    
    formatted = []
    for row in res.data:
        session_a = row.get("doc_a", {}).get("session_id", "") if row.get("doc_a") else ""
        session_b = row.get("doc_b", {}).get("session_id", "") if row.get("doc_b") else ""
        
        formatted.append({
            "id": row.get("id"),
            "session_a": session_a,
            "session_b": session_b,
            "summary": row.get("summary") or "Decision Comparison",
            "created_at": row.get("created_at")
        })
        
    return formatted
