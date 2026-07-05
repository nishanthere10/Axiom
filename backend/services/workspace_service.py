from typing import List, Dict, Any, Optional
import asyncio
from services.db import get_supabase

def create_workspace(user_id: str, name: str, description: Optional[str] = None, icon: Optional[str] = None) -> Dict[str, Any]:
    supabase = get_supabase()
    response = supabase.table("workspaces").insert({
        "user_id": user_id,
        "name": name,
        "description": description,
        "icon": icon
    }).execute()
    workspace = response.data[0]
    
    supabase.table("workspace_members").insert({
        "workspace_id": workspace["id"],
        "user_id": user_id,
        "role": "owner"
    }).execute()
    
    return workspace

def get_workspaces(user_id: str) -> List[Dict[str, Any]]:
    supabase = get_supabase()
    response = supabase.table("workspaces").select("*").eq("user_id", user_id).is_("deleted_at", "null").execute()
    return response.data

def get_workspace(workspace_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase()
    response = supabase.table("workspaces").select("*").eq("id", workspace_id).eq("user_id", user_id).is_("deleted_at", "null").execute()
    if not response.data:
        return None
    return response.data[0]

def update_workspace(workspace_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    supabase = get_supabase()
    response = supabase.table("workspaces").update(updates).eq("id", workspace_id).eq("user_id", user_id).is_("deleted_at", "null").execute()
    if not response.data:
        return None
    return response.data[0]

def delete_workspace(workspace_id: str, user_id: str) -> bool:
    supabase = get_supabase()
    from datetime import datetime
    response = supabase.table("workspaces").update({
        "deleted_at": datetime.utcnow().isoformat()
    }).eq("id", workspace_id).eq("user_id", user_id).is_("deleted_at", "null").execute()
    return len(response.data) > 0

async def get_workspace_dashboard(workspace_id: str, user_id: str) -> Dict[str, Any]:
    supabase = get_supabase()

    # 1. Verify workspace exists and belongs to user
    workspace = get_workspace(workspace_id, user_id)
    if not workspace:
        return None

    # Helper function to run sync supabase queries in thread
    async def fetch_table(table: str, select: str = "*", filters: Dict[str, Any] = None, order_by: str = "created_at", limit: int = None):
        def _query():
            q = supabase.table(table).select(select)
            if filters:
                for k, v in filters.items():
                    if k == "workspace_id":
                        q = q.eq("workspace_id", workspace_id)
                    elif k == "user_id":
                        q = q.eq("user_id", user_id)
                    else:
                        q = q.eq(k, v)
            if order_by:
                q = q.order(order_by, desc=True)
            if limit:
                q = q.limit(limit)
            return q.execute()
        
        try:
            res = await asyncio.to_thread(_query)
            return res.data
        except Exception:
            return []

    # Parallel queries for lists
    results = await asyncio.gather(
        fetch_table("decision_records", filters={"workspace_id": workspace_id, "created_by": user_id}, limit=5),
        fetch_table("research_sessions", filters={"workspace_id": workspace_id, "user_id": user_id}, limit=5),
        fetch_table("comparisons", filters={"workspace_id": workspace_id, "user_id": user_id}, limit=5),
        fetch_table("github_repositories", filters={"user_id": user_id, "is_active": True}, order_by="last_synced_at", limit=5),
    )
    
    recent_decisions = results[0]
    recent_research = results[1]
    recent_comparisons = results[2]
    connected_repos = results[3]

    # Parallel queries for counts (We fetch all minimal fields to count, or use exact count if supported, but len() is safe for small numbers or we use specific queries)
    # Since supabase-py has a count method: `select("id", count="exact")`, we can do that for optimization.
    async def fetch_count(table: str, filters: Dict[str, Any] = None):
        def _count():
            q = supabase.table(table).select("id", count="exact")
            if filters:
                for k, v in filters.items():
                    if k == "workspace_id":
                        q = q.eq("workspace_id", workspace_id)
                    elif k == "user_id":
                        q = q.eq("user_id", user_id)
                    else:
                        q = q.eq(k, v)
            return q.execute()
        try:
            res = await asyncio.to_thread(_count)
            return res.count if hasattr(res, 'count') and res.count is not None else len(res.data)
        except Exception:
            return 0
            
    async def fetch_decisions_by_status():
        def _fetch():
            return supabase.table("decision_records").select("status").eq("workspace_id", workspace_id).eq("created_by", user_id).execute()
        try:
            res = await asyncio.to_thread(_fetch)
            return res.data
        except Exception:
            return []

    counts = await asyncio.gather(
        fetch_count("research_sessions", {"workspace_id": workspace_id, "user_id": user_id}),
        fetch_count("comparisons", {"workspace_id": workspace_id, "user_id": user_id}),
        fetch_count("github_repositories", {"user_id": user_id, "is_active": True}),
        fetch_decisions_by_status(),
        fetch_count("memory_items", {"user_id": user_id, "scope": "global"}),
        fetch_count("memory_items", {"user_id": user_id, "scope": f"workspace:{workspace_id}"}),
        fetch_count("memory_items", {"user_id": user_id, "is_pinned": True})
    )
    
    total_research = counts[0]
    total_comparisons = counts[1]
    total_repos = counts[2]
    all_decisions = counts[3]
    global_memories = counts[4]
    workspace_memories = counts[5]
    pinned_memories = counts[6]
    
    # Calculate Decision Summary
    decision_summary = {"proposed": 0, "approved": 0, "implemented": 0, "rejected": 0, "archived": 0}
    for d in all_decisions:
        status = d.get("status", "proposed").lower()
        if status in decision_summary:
            decision_summary[status] += 1
            
    # Calculate Memory Summary
    memory_summary = {
        "global_memories": global_memories,
        "workspace_memories": workspace_memories,
        "pinned_memories": pinned_memories
    }
            
    # Quick Insights
    most_common_cat = None
    if all_decisions:
        # We didn't fetch category in all_decisions, but we can just use recent_decisions for insights
        categories = [d.get("category") for d in recent_decisions if d.get("category")]
        if categories:
            most_common_cat = max(set(categories), key=categories.count)
            
    quick_insights = {
        "most_common_decision_category": most_common_cat,
        "most_referenced_repository": connected_repos[0]["repository_name"] if connected_repos else None,
        "most_active_research_area": None
    }

    return {
        "workspace": workspace,
        "decision_summary": decision_summary,
        "research_summary": {"total_sessions": total_research, "active_sessions": 0},
        "repository_summary": {"connected_repos": total_repos},
        "memory_summary": memory_summary,
        "comparison_summary": {"total_comparisons": total_comparisons},
        "recent_decisions": recent_decisions,
        "recent_research": recent_research,
        "recent_comparisons": recent_comparisons,
        "connected_repositories": connected_repos,
        "quick_insights": quick_insights
    }
