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
    # Fetch workspace IDs + roles where the user is a member
    memberships = supabase.table("workspace_members").select("workspace_id, role").eq("user_id", user_id).execute()
    if not memberships.data:
        return []
    
    role_map = {m["workspace_id"]: m["role"] for m in memberships.data}
    workspace_ids = list(role_map.keys())
    
    # Fetch the workspaces matching those IDs
    response = supabase.table("workspaces").select("*").in_("id", workspace_ids).is_("deleted_at", "null").execute()
    
    # Fetch member counts for these workspaces to identify shared team workspaces
    all_members = supabase.table("workspace_members").select("workspace_id").in_("workspace_id", workspace_ids).execute()
    member_counts = {}
    for m in (all_members.data or []):
        wid = m["workspace_id"]
        member_counts[wid] = member_counts.get(wid, 0) + 1

    # Inject user_role, is_shared, member_count, and has_team_members into each workspace dict
    result = []
    for ws in response.data:
        ws["user_role"] = role_map.get(ws["id"], "member")
        ws["is_shared"] = ws.get("user_id") != user_id
        ws["member_count"] = member_counts.get(ws["id"], 1)
        ws["has_team_members"] = ws["member_count"] > 1
        result.append(ws)
    return result

def get_workspace(workspace_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    supabase = get_supabase()
    # Check if user is a member
    member_check = supabase.table("workspace_members").select("id").eq("workspace_id", workspace_id).eq("user_id", user_id).execute()
    if not member_check.data:
        return None
        
    response = supabase.table("workspaces").select("*").eq("id", workspace_id).is_("deleted_at", "null").execute()
    if not response.data:
        return None
    return response.data[0]

def update_workspace(workspace_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    supabase = get_supabase()
    # Check if user has permission
    member_check = supabase.table("workspace_members").select("role").eq("workspace_id", workspace_id).eq("user_id", user_id).execute()
    if not member_check.data or member_check.data[0].get("role") == "viewer":
        return None
        
    response = supabase.table("workspaces").update(updates).eq("id", workspace_id).is_("deleted_at", "null").execute()
    if not response.data:
        return None
    return response.data[0]

def delete_workspace(workspace_id: str, user_id: str) -> bool:
    supabase = get_supabase()
    # Check if user is owner
    member_check = supabase.table("workspace_members").select("role").eq("workspace_id", workspace_id).eq("user_id", user_id).execute()
    if not member_check.data or member_check.data[0].get("role") != "owner":
        return False
        
    from datetime import datetime
    response = supabase.table("workspaces").update({
        "deleted_at": datetime.utcnow().isoformat()
    }).eq("id", workspace_id).is_("deleted_at", "null").execute()
    return len(response.data) > 0

# 🔐 FIX 3.1: N+1 Query Optimization
# Use single RPC function instead of 6+ separate queries
# Reduces round-trips from 6+ to 1, eliminates N+1 problem
# Falls back to old logic if RPC not deployed yet
async def get_workspace_dashboard(workspace_id: str, user_id: str) -> Dict[str, Any]:
    supabase = get_supabase()
    
    # Try RPC first (optimized path)
    def _rpc_call():
        return supabase.rpc(
            'get_workspace_dashboard_data',
            {'p_workspace_id': workspace_id, 'p_user_id': user_id}
        ).execute()
    
    try:
        result = await asyncio.to_thread(_rpc_call)
        if result.data:
            return result.data
    except Exception as e:
        # RPC not deployed or failed, fall back to old queries
        pass
    
    # FALLBACK: Old N+1 query logic (remove after migration deployed)
    workspace = get_workspace(workspace_id, user_id)
    if not workspace:
        return None

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

    async def fetch_repos_with_profiles():
        def _q():
            return supabase.table("github_repositories").select(
                "id, repository_name, repository_owner, last_sync_at, indexed_file_count, total_file_count, github_repository_profiles(tech_stack, architecture_summary)"
            ).eq("workspace_id", workspace_id).eq("is_active", True).order("created_at", desc=True).limit(5).execute()
        try:
            res = await asyncio.to_thread(_q)
            repos = []
            for r in res.data:
                prof = r.get("github_repository_profiles", [])
                repos.append({
                    "id": r.get("id"),
                    "repository_name": r.get("repository_name"),
                    "repository_owner": r.get("repository_owner"),
                    "last_sync_at": r.get("last_sync_at"),
                    "indexed_file_count": r.get("indexed_file_count"),
                    "total_file_count": r.get("total_file_count"),
                    "profile": prof[0] if prof else None
                })
            return repos
        except Exception:
            return []

    results = await asyncio.gather(
        fetch_table("decision_records", filters={"workspace_id": workspace_id}, limit=5),
        fetch_table("research_sessions", filters={"workspace_id": workspace_id}, limit=5),
        fetch_table("comparisons", filters={"workspace_id": workspace_id}, limit=5),
        fetch_repos_with_profiles(),
    )
    
    recent_decisions = results[0]
    recent_research = results[1]
    recent_comparisons = results[2]
    connected_repos = results[3]

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
            return supabase.table("decision_records").select("status").eq("workspace_id", workspace_id).execute()
        try:
            res = await asyncio.to_thread(_fetch)
            return res.data
        except Exception:
            return []

    counts = await asyncio.gather(
        fetch_count("research_sessions", {"workspace_id": workspace_id}),
        fetch_count("comparisons", {"workspace_id": workspace_id}),
        fetch_count("github_repositories", {"workspace_id": workspace_id, "is_active": True}),
        fetch_decisions_by_status(),
        fetch_count("memory_items", {"scope": "global"}),
        fetch_count("memory_items", {"scope": f"workspace:{workspace_id}"}),
        fetch_count("memory_items", {"workspace_id": workspace_id, "is_pinned": True})
    )
    
    total_research = counts[0]
    total_comparisons = counts[1]
    total_repos = counts[2]
    all_decisions = counts[3]
    global_memories = counts[4]
    workspace_memories = counts[5]
    pinned_memories = counts[6]
    
    decision_summary = {"proposed": 0, "approved": 0, "implemented": 0, "rejected": 0, "archived": 0}
    for d in all_decisions:
        status = d.get("status", "proposed").lower()
        if status in decision_summary:
            decision_summary[status] += 1
            
    memory_summary = {
        "global_memories": global_memories,
        "workspace_memories": workspace_memories,
        "pinned_memories": pinned_memories
    }
            
    most_common_cat = None
    if all_decisions:
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

async def get_workspace_activity(workspace_id: str, user_id: str, limit: int = 20) -> list[dict]:
    """
    Returns a unified activity feed mixing research sessions, decisions, and comparisons
    sorted by most recent. Used for the workspace dashboard activity timeline.
    """
    import asyncio
    from services.db import get_supabase
    supabase = get_supabase()

    async def _fetch(table: str, select: str, label: str):
        def _q():
            return supabase.table(table).select(select).eq("workspace_id", workspace_id).order("created_at", desc=True).limit(limit).execute()
        try:
            res = await asyncio.to_thread(_q)
            items = []
            for row in (res.data or []):
                items.append({
                    "type": label,
                    "id": row.get("id"),
                    "title": row.get("question") or row.get("title") or row.get("summary", ""),
                    "status": row.get("status", ""),
                    "created_at": row.get("created_at"),
                })
            return items
        except Exception:
            return []

    results = await asyncio.gather(
        _fetch("research_sessions", "id, question, status, created_at", "research"),
        _fetch("decision_records", "id, title, status, created_at", "decision"),
        _fetch("comparisons", "id, summary, created_at", "comparison"),
    )

    all_items = results[0] + results[1] + results[2]
    all_items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return all_items[:limit]
