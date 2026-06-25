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

class DecisionSummary(BaseModel):
    proposed: int = 0
    approved: int = 0
    implemented: int = 0
    rejected: int = 0
    archived: int = 0

class ResearchSummary(BaseModel):
    total_sessions: int = 0
    active_sessions: int = 0

class RepositorySummary(BaseModel):
    connected_repos: int = 0

class MemorySummary(BaseModel):
    global_memories: int = 0
    workspace_memories: int = 0
    pinned_memories: int = 0

class ComparisonSummary(BaseModel):
    total_comparisons: int = 0

class QuickInsights(BaseModel):
    most_common_decision_category: Optional[str] = None
    most_referenced_repository: Optional[str] = None
    most_active_research_area: Optional[str] = None

class WorkspaceDashboardResponse(BaseModel):
    workspace: WorkspaceResponse
    decision_summary: DecisionSummary
    research_summary: ResearchSummary
    repository_summary: RepositorySummary
    memory_summary: MemorySummary
    comparison_summary: ComparisonSummary
    recent_decisions: List[dict]
    recent_research: List[dict]
    recent_comparisons: List[dict]
    connected_repositories: List[dict]
    quick_insights: QuickInsights
