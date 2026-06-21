from fastapi import APIRouter, Depends, HTTPException, Header
from core.auth import get_current_user
from api.schemas.workspaces import WorkspaceCreate, WorkspaceUpdate, WorkspaceResponse, WorkspaceListResponse
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
def get_workspace(workspace_id: str, user_id: str = Depends(get_current_user)):
    """
    GET /workspaces/{id}
    Get a specific workspace.
    """
    workspace = workspace_service.get_workspace(workspace_id, user_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return WorkspaceResponse(**workspace)

@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
def update_workspace(workspace_id: str, body: WorkspaceUpdate, user_id: str = Depends(get_current_user)):
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
def delete_workspace(workspace_id: str, user_id: str = Depends(get_current_user)):
    """
    DELETE /workspaces/{id}
    Soft delete a workspace.
    """
    success = workspace_service.delete_workspace(workspace_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workspace not found or unauthorized")
    return None
