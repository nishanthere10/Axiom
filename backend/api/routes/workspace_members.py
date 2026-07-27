from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from core.auth import get_current_user, verify_workspace_path
from services.db import get_supabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class MemberResponse(BaseModel):
    id: str
    workspace_id: str
    user_id: str
    role: str
    created_at: str

class InviteMemberRequest(BaseModel):
    user_id: str
    role: str = "member"

class UpdateMemberRequest(BaseModel):
    role: str

@router.get("", response_model=List[MemberResponse])
def list_workspace_members(
    workspace_id: str,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path)
):
    """List all members of a workspace"""
    supabase = get_supabase()
    response = supabase.table("workspace_members").select("*").eq("workspace_id", workspace_id).execute()
    return response.data

@router.post("", response_model=MemberResponse)
def invite_workspace_member(
    workspace_id: str,
    body: InviteMemberRequest,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path)
):
    """Invite a new member to the workspace. Must be an owner to do this."""
    supabase = get_supabase()
    
    # Check if current user is owner
    owner_check = supabase.table("workspace_members").select("role").eq("workspace_id", workspace_id).eq("user_id", user_id).limit(1).execute()
    if not owner_check.data or owner_check.data[0].get("role") != "owner":
        raise HTTPException(status_code=403, detail="Only owners can invite members")
        
    try:
        response = supabase.table("workspace_members").insert({
            "workspace_id": workspace_id,
            "user_id": body.user_id,
            "role": body.role
        }).execute()
        return response.data[0]
    except Exception as e:
        logger.error("Error inviting member: %s", e)
        raise HTTPException(status_code=400, detail="Could not invite member. They may already be in the workspace.")

@router.delete("/{target_user_id}")
def remove_workspace_member(
    workspace_id: str,
    target_user_id: str,
    user_id: str = Depends(get_current_user),
    _ws: str = Depends(verify_workspace_path)
):
    """Remove a member from the workspace. Must be an owner."""
    supabase = get_supabase()
    
    # Check if current user is owner
    owner_check = supabase.table("workspace_members").select("role").eq("workspace_id", workspace_id).eq("user_id", user_id).limit(1).execute()
    if not owner_check.data or owner_check.data[0].get("role") != "owner":
        raise HTTPException(status_code=403, detail="Only owners can remove members")
        
    # Prevent removing oneself if they are the only owner
    if target_user_id == user_id:
        owners = supabase.table("workspace_members").select("id").eq("workspace_id", workspace_id).eq("role", "owner").execute()
        if len(owners.data) <= 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last owner")

    response = supabase.table("workspace_members").delete().eq("workspace_id", workspace_id).eq("user_id", target_user_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Member not found")
        
    return {"status": "success", "message": "Member removed"}
