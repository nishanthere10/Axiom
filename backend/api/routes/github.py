from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List
from pydantic import BaseModel
import httpx
import logging

from core.auth import get_current_user
from services.db import supabase
from services.context_providers.github_provider import github_provider

router = APIRouter(prefix="/github", tags=["github"])
logger = logging.getLogger(__name__)

class SelectRepoRequest(BaseModel):
    repository_id: str
    repository_name: str
    repository_owner: str
    repository_url: str
    is_private: bool

@router.post("/connect")
async def connect_github(user_id: str = Depends(get_current_user)):
    """
    Verify and register the GitHub connection via Clerk.
    """
    token = await github_provider.get_token(user_id)
    if not token:
        raise HTTPException(status_code=400, detail="No GitHub account connected in Clerk.")
        
    # Upsert connection record
    supabase.table("github_connections").upsert({
        "user_id": user_id,
        "github_username": "connected_via_clerk" # Would fetch from GitHub API for real
    }).execute()
    
    return {"status": "success", "message": "GitHub connected successfully"}

@router.get("/repositories")
async def list_repositories(user_id: str = Depends(get_current_user)):
    """
    List repositories accessible by the user's GitHub token.
    """
    token = await github_provider.get_token(user_id)
    if not token:
        raise HTTPException(status_code=401, detail="GitHub not connected")
        
    try:
        async with httpx.AsyncClient() as client:
            # Fetch user repos
            r = await client.get("https://api.github.com/user/repos?per_page=100&sort=updated", headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json"
            })
            r.raise_for_status()
            repos = r.json()
            
            # Fetch already selected repos
            selected_res = supabase.table("github_repositories").select("repository_id").eq("user_id", user_id).execute()
            selected_ids = [row["repository_id"] for row in selected_res.data]
            
            formatted_repos = []
            for repo in repos:
                formatted_repos.append({
                    "id": str(repo["id"]),
                    "name": repo["name"],
                    "owner": repo["owner"]["login"],
                    "full_name": repo["full_name"],
                    "url": repo["html_url"],
                    "private": repo["private"],
                    "selected": str(repo["id"]) in selected_ids
                })
            return {"repositories": formatted_repos}
    except Exception as e:
        logger.error(f"Failed to list repositories: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch repositories from GitHub")

@router.post("/repositories/select")
async def select_repository(req: SelectRepoRequest, user_id: str = Depends(get_current_user)):
    """
    Mark a repository for sync/usage.
    """
    supabase.table("github_repositories").upsert({
        "user_id": user_id,
        "repository_id": req.repository_id,
        "repository_name": req.repository_name,
        "repository_owner": req.repository_owner,
        "repository_url": req.repository_url,
        "is_private": req.is_private,
        "is_active": True
    }, on_conflict="user_id, repository_id").execute()
    
    return {"status": "success"}

async def sync_repo_background(user_id: str, repository_id: str, owner: str, repo_name: str, job_id: str):
    """Background task to run the sync"""
    import datetime
    
    supabase.table("github_sync_jobs").update({"status": "running"}).eq("id", job_id).execute()
    
    resource_id = f"{owner}/{repo_name}"
    success = await github_provider.sync(user_id, resource_id)
    
    status = "completed" if success else "failed"
    supabase.table("github_sync_jobs").update({
        "status": status,
        "completed_at": datetime.datetime.utcnow().isoformat()
    }).eq("id", job_id).execute()
    
    if success:
        supabase.table("github_repositories").update({
            "last_synced_at": datetime.datetime.utcnow().isoformat()
        }).eq("user_id", user_id).eq("repository_id", repository_id).execute()

@router.post("/repositories/{repository_id}/sync")
async def sync_repository(repository_id: str, background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user)):
    """
    Trigger a background sync for a selected repository.
    """
    # Verify repo exists
    res = supabase.table("github_repositories").select("*").eq("user_id", user_id).eq("repository_id", repository_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Repository not found or not selected")
        
    repo = res.data[0]
    
    # Create sync job
    job_res = supabase.table("github_sync_jobs").insert({
        "user_id": user_id,
        "repository_id": repository_id,
        "status": "queued"
    }).execute()
    
    job_id = job_res.data[0]["id"]
    
    background_tasks.add_task(
        sync_repo_background, 
        user_id, 
        repository_id, 
        repo["repository_owner"], 
        repo["repository_name"], 
        job_id
    )
    
    return {"status": "queued", "job_id": job_id}

@router.get("/status")
async def get_github_status(user_id: str = Depends(get_current_user)):
    conn_res = supabase.table("github_connections").select("*").eq("user_id", user_id).execute()
    is_connected = len(conn_res.data) > 0
    
    repos_res = supabase.table("github_repositories").select("*").eq("user_id", user_id).eq("is_active", True).execute()
    active_repos = repos_res.data
    
    return {
        "is_connected": is_connected,
        "active_repositories": active_repos
    }
