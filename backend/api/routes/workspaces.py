from fastapi import APIRouter, Depends, HTTPException, Header
from core.auth import get_current_user, verify_workspace_path
from api.schemas.workspaces import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse, WorkspaceListResponse, WorkspaceDashboardResponse
from services import workspace_service

router = APIRouter()

@router.post("", response_model=WorkspaceResponse, status_code=201)
def create_workspace(body: WorkspaceCreate, user_id: str = Depends(get_current_user)):
    """
    POST /workspaces
    Create a new workspace.
    """
    workspace = workspace_service.create_workspace(
        user_id=user_id,
        name=body.name,
        description=body.description,
        icon=body.icon
    )
    return WorkspaceResponse(**workspace)

@router.get("", response_model=WorkspaceListResponse)
def list_workspaces(user_id: str = Depends(get_current_user)):
    """
    GET /workspaces
    List all workspaces for the current user.
    """
    workspaces = workspace_service.get_workspaces(user_id)
    return WorkspaceListResponse(workspaces=[WorkspaceResponse(**w) for w in workspaces])

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
def get_workspace(workspace_id: str, user_id: str = Depends(get_current_user), _ws: str = Depends(verify_workspace_path)):
    """
    GET /workspaces/{id}
    Get a specific workspace.
    """
    workspace = workspace_service.get_workspace(workspace_id, user_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse(**workspace)

@router.get("/{workspace_id}/dashboard", response_model=WorkspaceDashboardResponse)
async def get_workspace_dashboard(workspace_id: str, user_id: str = Depends(get_current_user), _ws: str = Depends(verify_workspace_path)):
    """
    GET /workspaces/{id}/dashboard
    Get the aggregated dashboard data for a workspace.
    """
    dashboard_data = await workspace_service.get_workspace_dashboard(workspace_id, user_id)
    if not dashboard_data:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return dashboard_data

@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(workspace_id: str, body: WorkspaceUpdate, user_id: str = Depends(get_current_user), _ws: str = Depends(verify_workspace_path)):
    """
    PATCH /workspaces/{id}
    Update a workspace.
    """
    updates = body.dict(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    
    workspace = workspace_service.update_workspace(workspace_id, user_id, updates)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found or unauthorized")
    
    return WorkspaceResponse(**workspace)

@router.delete("/{workspace_id}", status_code=204)
def delete_workspace(workspace_id: str, user_id: str = Depends(get_current_user), _ws: str = Depends(verify_workspace_path)):
    """
    DELETE /workspaces/{id}
    Soft delete a workspace.
    """
    success = workspace_service.delete_workspace(workspace_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found or unauthorized")
    return None

@router.get("/{workspace_id}/activity")
async def get_workspace_activity(workspace_id: str, limit: int = 20, user_id: str = Depends(get_current_user), _ws: str = Depends(verify_workspace_path)):
    """
    GET /workspaces/{id}/activity
    Returns a unified activity feed for the workspace dashboard.
    """
    activity = await workspace_service.get_workspace_activity(workspace_id, user_id, limit)
    return {"activity": activity}
