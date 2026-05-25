import difflib
from datetime import datetime, timezone
from services.db import supabase
from typing import List, Dict, Any

def text_similarity(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

def time_proximity(dt1: datetime, dt2: datetime) -> float:
    diff_days = abs((dt1 - dt2).total_seconds()) / (60 * 60 * 24)
    # 0 days = 1.0, 30+ days = 0.0
    return max(0.0, 1.0 - (diff_days / 30.0))

def get_suggestions(session_id: str) -> List[Dict[str, Any]]:
    # 1. Fetch the target session
    res = supabase.table("decision_documents").select("*").eq("session_id", session_id).execute()
    if not res.data:
        return []
    target = res.data[0]
    
    # 2. Fetch all other sessions (ideally limit this in a real app, but for V1 we fetch all)
    res_all = supabase.table("decision_documents").select("*").neq("session_id", session_id).execute()
    if not res_all.data:
        return []
        
    target_dt = datetime.fromisoformat(target["created_at"].replace("Z", "+00:00"))
    
    suggestions = []
    for doc in res_all.data:
        doc_dt = datetime.fromisoformat(doc["created_at"].replace("Z", "+00:00"))
        
        q_sim = text_similarity(target.get("question", ""), doc.get("question", ""))
        r_sim = text_similarity(target.get("recommendation_context", ""), doc.get("recommendation_context", ""))
        t_prox = time_proximity(target_dt, doc_dt)
        
        score = (0.5 * q_sim) + (0.3 * r_sim) + (0.2 * t_prox)
        
        suggestions.append({
            "session_id": doc["session_id"],
            "question": doc.get("question", "Unknown Question"),
            "created_at": doc.get("created_at"),
            "score": round(score, 3)
        })
        
    # Sort descending by score and take top 5
    suggestions.sort(key=lambda x: x["score"], reverse=True)
    return suggestions[:5]
