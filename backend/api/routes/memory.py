from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel
from services import memory_service
from api.schemas.memory import MemoryItemResponse

router = APIRouter()

class MemoryListResponse(BaseModel):
    memories: List[MemoryItemResponse]

class MemoryDetailResponse(BaseModel):
    memory: MemoryItemResponse

class PromoteMemoryRequest(BaseModel):
    memory_id: str

class PromoteMemoryResponse(BaseModel):
    promoted: bool

@router.get("", response_model=MemoryListResponse)
def get_all_memories():
    """
    GET /memory
    Returns all active memories (permanent and unexpired temporary).
    """
    memories = memory_service.get_active_memories(limit=100)
    return MemoryListResponse(memories=memories)

@router.get("/{memory_id}", response_model=MemoryDetailResponse)
def get_memory(memory_id: str):
    """
    GET /memory/{id}
    Returns details for a specific memory.
    """
    memory = memory_service.get_memory_by_id(memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory not found")
    return MemoryDetailResponse(memory=memory)

@router.post("/promote", response_model=PromoteMemoryResponse)
def promote_memory(body: PromoteMemoryRequest):
    """
    POST /memory/promote
    Promotes a temporary memory to permanent status.
    """
    success = memory_service.promote_memory(body.memory_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to promote memory (maybe not found or already permanent).")
    return PromoteMemoryResponse(promoted=True)
