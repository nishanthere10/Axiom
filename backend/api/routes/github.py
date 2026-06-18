from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import httpx
import logging
import asyncio

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

@router.get("/repositories/{repository_id}/files")
async def list_repository_files(repository_id: str, user_id: str = Depends(get_current_user)):
    """
    Get all .md files in the repository grouped by folder.
    """
    res = supabase.table("github_repositories").select("*").eq("user_id", user_id).eq("repository_id", repository_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    repo = res.data[0]
    token = await github_provider.get_token(user_id)
    if not token:
        raise HTTPException(status_code=401, detail="GitHub not connected")
        
    tree = await github_provider.get_file_tree(token, repo["repository_owner"], repo["repository_name"])
    
    # Cache all the paths so the subsequent sync doesn't need to re-fetch the tree
    md_paths = []
    for f in tree.get("folders", []):
        md_paths.extend(f.get("files", []))
    
    if md_paths:
        try:
            def update_cache():
                supabase.table("github_repositories").update({
                    "cached_file_paths": md_paths
                }).eq("repository_id", repository_id).execute()
            await asyncio.to_thread(update_cache)
        except Exception as e:
            logger.warning(f"Failed to cache github tree: {e}")
            
    return tree

class SyncRepoRequest(BaseModel):
    selected_folders: List[str] = []
    total_files: int = 0

async def sync_repo_background(user_id: str, repository_id: str, owner: str, repo_name: str, job_id: str, selected_folders: List[str], prefetched_paths: Optional[List[str]] = None):
    """Background task to run the sync with real-time progress updates"""
    import datetime
    
    logger.info(f"[GITHUB SYNC] Starting sync job {job_id} for {owner}/{repo_name}")
    supabase.table("github_sync_jobs").update({"status": "running"}).eq("id", job_id).execute()
    
    # Define a progress callback that updates Supabase
    async def progress_callback(file_path: str):
        def update_db():
            job_res = supabase.table("github_sync_jobs").select("progress_current").eq("id", job_id).execute()
            current = job_res.data[0].get("progress_current", 0) + 1
            supabase.table("github_sync_jobs").update({
                "progress_current": current,
                "last_file": file_path
            }).eq("id", job_id).execute()
        try:
            await asyncio.to_thread(update_db)
        except Exception as e:
            logger.warning(f"Failed to update progress for job {job_id}: {e}")

    try:
        resource_id = f"{owner}/{repo_name}"
        success = await github_provider.sync(
            user_id, 
            resource_id, 
            selected_folders=selected_folders,
            progress_callback=progress_callback,
            prefetched_paths=prefetched_paths
        )
    except Exception as e:
        logger.error(f"[GITHUB SYNC] Exception during sync: {e}", exc_info=True)
        success = False
    
    status = "completed" if success else "failed"
    logger.info(f"[GITHUB SYNC] Job {job_id} finished with status: {status}")
    supabase.table("github_sync_jobs").update({
        "status": status,
        "completed_at": datetime.datetime.utcnow().isoformat()
    }).eq("id", job_id).execute()
    
    if success:
        supabase.table("github_repositories").update({
            "last_synced_at": datetime.datetime.utcnow().isoformat()
        }).eq("user_id", user_id).eq("repository_id", repository_id).execute()

@router.post("/repositories/{repository_id}/sync")
async def sync_repository(repository_id: str, req: SyncRepoRequest, background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user)):
    """
    Trigger a background sync for selected folders in a repository.
    """
    res = supabase.table("github_repositories").select("*").eq("user_id", user_id).eq("repository_id", repository_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Repository not found")
        
    repo = res.data[0]
    
    # Store selected_paths in the repository table for future re-syncs
    supabase.table("github_repositories").update({
        "selected_paths": req.selected_folders
    }).eq("repository_id", repository_id).execute()
    
    # Create sync job with progress trackers
    job_res = supabase.table("github_sync_jobs").insert({
        "user_id": user_id,
        "repository_id": repository_id,
        "status": "queued",
        "progress_total": req.total_files,
        "progress_current": 0,
        "selected_paths": req.selected_folders
    }).execute()
    
    job_id = job_res.data[0]["id"]
    
    background_tasks.add_task(
        sync_repo_background, 
        user_id, 
        repository_id, 
        repo["repository_owner"], 
        repo["repository_name"], 
        job_id,
        req.selected_folders,
        repo.get("cached_file_paths")
    )
    
    return {"status": "queued", "job_id": job_id}

@router.get("/sync-jobs/{job_id}/progress")
async def get_sync_job_progress(job_id: str, user_id: str = Depends(get_current_user)):
    """
    Returns real-time progress for a specific sync job.
    """
    import uuid
    
    try:
        valid_uuid = uuid.UUID(str(job_id))
    except ValueError:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid job_id format: '{job_id}'. Expected a valid UUID."
        )

    res = supabase.table("github_sync_jobs").select("*").eq("id", str(valid_uuid)).eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Job not found")
        
    job = res.data[0]
    total = job.get("progress_total", 0)
    current = job.get("progress_current", 0)
    
    percent = (current / total * 100) if total > 0 else 0
    
    return {
        "status": job["status"],
        "progress_current": current,
        "progress_total": total,
        "percent": min(int(percent), 100),
        "last_file": job.get("last_file")
    }

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
