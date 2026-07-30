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
async def get_workspace_dashboard(workspace_id: str, user_id: str) -> Dict[str, Any]:
    supabase = get_supabase()
    
    def _rpc_call():
        return supabase.rpc(
            'get_workspace_dashboard_data',
            {'p_workspace_id': workspace_id, 'p_user_id': user_id}
        ).execute()
    
    try:
        result = await asyncio.to_thread(_rpc_call)
        return result.data if result.data else None
    except Exception as e:
        # Fallback: if RPC not deployed yet, return None
        return None

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
