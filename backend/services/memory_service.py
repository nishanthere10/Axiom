import logging
from services.db import supabase
from api.schemas.memory import MemoryItemCreate, MemoryScope, MemoryType
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def create_memory_item(data: MemoryItemCreate) -> Optional[Dict[str, Any]]:
    """Creates a memory item in Supabase."""
    
    # Calculate expiration for temporary memories
    expires_at = data.expires_at
    if data.scope == "temporary" and not expires_at:
        expires_at = datetime.utcnow() + timedelta(days=30)
        
    payload = {
        "memory_type": data.memory_type,
        "source_id": data.source_id,
        "source_type": data.source_type,
        "summary": data.summary,
        "metadata": data.metadata,
        "scope": data.scope,
        "is_active": True,
        "expires_at": expires_at.isoformat() if expires_at else None
    }
    
    try:
        response = supabase.table("memory_items").insert(payload).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.error("Error creating memory item in Supabase: %s", e, exc_info=True)
    return None

def get_active_memories(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves all active memories."""
    now = datetime.utcnow().isoformat()
    try:
        # Get permanent memories, or temporary ones that haven't expired
        response = supabase.table("memory_items").select("*").eq("is_active", True).order("created_at", desc=True).limit(limit).execute()
        
        valid_memories = []
        for row in response.data:
            if row.get("scope") == "permanent":
                valid_memories.append(row)
            elif row.get("expires_at"):
                # Check expiration
                if row["expires_at"] > now:
                    valid_memories.append(row)
                else:
                    # Mark as inactive? Let's just filter it out for now.
                    pass
            else:
                valid_memories.append(row)
                
        return valid_memories
    except Exception as e:
        logger.error("Error fetching memories: %s", e, exc_info=True)
        return []

def promote_memory(memory_id: str) -> bool:
    """Promotes a memory from temporary to permanent."""
    try:
        response = supabase.table("memory_items").update({
            "scope": "permanent",
            "expires_at": None
        }).eq("id", memory_id).execute()
        return len(response.data) > 0
    except Exception as e:
        logger.error("Error promoting memory: %s", e, exc_info=True)
        return False

def get_memory_by_id(memory_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = supabase.table("memory_items").select("*").eq("id", memory_id).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.error("Error fetching memory %s: %s", memory_id, e, exc_info=True)
    return None
