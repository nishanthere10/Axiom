from typing import List, Dict, Any, Optional
from services.db import get_supabase

def create_workspace(user_id: str, name: str, description: Optional[str] = None, icon: Optional[str] = None) -> Dict[str, Any]:
    supabase = get_supabase()
    response = supabase.table("workspaces").insert({
        "user_id": user_id,
        "name": name,
        "description": description,
        "icon": icon
    }).execute()
    return response.data[0]

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
