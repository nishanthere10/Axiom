from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.auth import get_current_user, _decode_jwt_payload_unsafe
from services.db import get_supabase
from typing import Dict, Any

router = APIRouter()
security = HTTPBearer()

def get_admin_user(
    user_id: str = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials
    payload = _decode_jwt_payload_unsafe(token)
    
    # Check for admin role in Clerk public metadata or direct claim
    public_metadata = payload.get("publicMetadata") or payload.get("public_metadata") or {}
    role = payload.get("role") or public_metadata.get("role")
    
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user_id

@router.get("/metrics/overview")
def get_metrics_overview(admin_id: str = Depends(get_admin_user)) -> Dict[str, Any]:
    supabase = get_supabase()
    # Get today's row from the materialized view
    res = supabase.table("analytics_daily_mv").select("*").order("metric_date", desc=True).limit(1).execute()
    
    if not res.data:
        return {
            "research_count": 0,
            "comparison_count": 0,
            "memory_hit_rate": 0.0,
            "avg_latency_ms": 0,
            "fallback_count": 0,
            "export_count": 0
        }
        
    row = res.data[0]
    searches = row.get("memory_search_count", 0)
    hits = row.get("memory_hit_count", 0)
    hit_rate = (hits / searches * 100) if searches > 0 else 0.0
    
    return {
        "research_count": row.get("research_count", 0),
        "comparison_count": row.get("comparison_count", 0),
        "memory_hit_rate": round(hit_rate, 2),
        "avg_latency_ms": row.get("avg_research_latency_ms", 0),
        "fallback_count": row.get("provider_fallback_count", 0),
        "export_count": row.get("export_count", 0)
    }

@router.get("/metrics/research")
def get_metrics_research(limit: int = 30, admin_id: str = Depends(get_admin_user)):
    supabase = get_supabase()
    res = supabase.table("analytics_daily_mv").select("metric_date, research_count, avg_research_latency_ms").order("metric_date", desc=True).limit(limit).execute()
    return {"data": res.data or []}

@router.get("/metrics/memory")
def get_metrics_memory(admin_id: str = Depends(get_admin_user)):
    supabase = get_supabase()
    res = supabase.table("analytics_daily_mv").select("metric_date, memory_retrieval_count, memory_hit_count, memory_search_count, avg_memory_latency_ms").order("metric_date", desc=True).limit(30).execute()
    return {"data": res.data or []}

@router.get("/metrics/providers")
def get_metrics_providers(admin_id: str = Depends(get_admin_user)):
    supabase = get_supabase()
    # Get provider stats for the last 30 days aggregated
    res = supabase.table("analytics_provider_mv").select("*").order("metric_date", desc=True).limit(100).execute()
    
    # We aggregate it for the frontend to be simple
    aggregated = {}
    data = res.data or []
    for row in data:
        p = row.get("provider_name")
        if not p: continue
        if p not in aggregated:
            aggregated[p] = {"requests": 0, "successes": 0, "failures": 0, "fallbacks": 0, "latency_sum": 0, "count": 0}
        
        aggregated[p]["requests"] += row.get("request_count", 0)
        aggregated[p]["successes"] += row.get("success_count", 0)
        aggregated[p]["failures"] += row.get("failure_count", 0)
        aggregated[p]["fallbacks"] += row.get("fallback_count", 0)
        
        if row.get("avg_latency_ms"):
            aggregated[p]["latency_sum"] += row["avg_latency_ms"]
            aggregated[p]["count"] += 1
            
    final_list = []
    for p, stats in aggregated.items():
        avg_lat = (stats["latency_sum"] / stats["count"]) if stats["count"] > 0 else 0
        final_list.append({
            "provider": p,
            "requests": stats["requests"],
            "failures": stats["failures"],
            "fallbacks": stats["fallbacks"],
            "avg_latency_ms": round(avg_lat)
        })
        
    return {"data": final_list}

@router.get("/metrics/topics")
def get_metrics_topics(admin_id: str = Depends(get_admin_user)):
    supabase = get_supabase()
    res = supabase.table("analytics_topic_mv").select("*").order("research_count", desc=True).limit(10).execute()
    
    data = res.data or []
    total_researches = sum(r.get("research_count", 0) for r in data)
    
    final_list = []
    for row in data:
        rc = row.get("research_count", 0)
        pct = (rc / total_researches * 100) if total_researches > 0 else 0
        final_list.append({
            "topic": row.get("topic_label"),
            "research_count": rc,
            "percentage": round(pct, 1)
        })
        
    return {"data": final_list}
