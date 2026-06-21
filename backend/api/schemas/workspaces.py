from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class WorkspaceCreate(BaseModel):
    name: str = Field(..., description="Name of the workspace")
    description: Optional[str] = Field(None, description="Optional description")
    icon: Optional[str] = Field(None, description="Optional icon or emoji")

class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None

class WorkspaceResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
class WorkspaceListResponse(BaseModel):
    workspaces: List[WorkspaceResponse]
