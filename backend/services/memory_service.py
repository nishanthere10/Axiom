import logging
from services.db import supabase
from api.schemas.memory import MemoryItemCreate, MemoryScope, MemoryType
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

import hashlib

def create_memory_item(data: MemoryItemCreate) -> Optional[Dict[str, Any]]:
    """Creates a memory item in Supabase, with deduplication based on summary."""
    
    # Compute dedup hash
    dedup_hash = hashlib.sha256(data.summary.strip().lower().encode()).hexdigest()

    # Check for existing active memory with same hash in this workspace
    try:
        existing = (
            supabase.table("memory_items")
            .select("id")
            .eq("user_id", data.user_id)
            .eq("workspace_id", data.workspace_id)
            .eq("dedup_hash", dedup_hash)
            .eq("is_active", True)
            .execute()
        )
        if existing.data:
            logger.info("Skipping duplicate memory (exact hash=%s...)", dedup_hash[:12])
            # Update last_used_at on the existing memory instead
            supabase.table("memory_items").update(
                {"last_used_at": datetime.utcnow().isoformat()}
            ).eq("id", existing.data[0]["id"]).execute()
            
            # Return existing memory item but mark it as skipped so caller knows
            existing_memory = existing.data[0]
            existing_memory["_dedup_skipped"] = True
            return existing_memory
    except Exception as e:
        logger.warning("Error checking for exact memory dedup hash: %s", e)

    # 2. Semantic vector deduplication check (threshold > 0.90)
    try:
        from services.pinecone_service import search_memories
        similar_memories = search_memories(
            query=data.summary,
            user_id=data.user_id,
            workspace_id=data.workspace_id,
            top_k=5,
            threshold=0.90,
            max_results=1
        )
        if similar_memories:
            dup_id = similar_memories[0].get("id") or similar_memories[0].get("metadata", {}).get("memory_id")
            if dup_id:
                logger.info("Skipping duplicate memory via semantic vector match (id=%s)", dup_id)
                try:
                    supabase.table("memory_items").update(
                        {"last_used_at": datetime.utcnow().isoformat()}
                    ).eq("id", dup_id).execute()
                except Exception:
                    pass
                return {"id": dup_id, "_dedup_skipped": True}
    except Exception as e:
        logger.warning("Error checking for semantic memory dedup: %s", e)
    
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
        "expires_at": expires_at.isoformat() if expires_at else None,
        "user_id": data.user_id,
        "workspace_id": data.workspace_id,
        "visibility": data.visibility,
        "dedup_hash": dedup_hash,
    }
    
    try:
        response = supabase.table("memory_items").insert(payload).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.error("Error creating memory item in Supabase: %s", e, exc_info=True)
    return None

def get_active_memories(user_id: str, workspace_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves all active memories for the user, including GLOBAL and matching WORKSPACE."""
    now = datetime.utcnow().isoformat()
    try:
        query = supabase.table("memory_items").select("*").eq("is_active", True).eq("user_id", user_id)
        if workspace_id:
            # We want GLOBAL memories OR WORKSPACE memories matching workspace_id
            query = query.or_(f"visibility.eq.GLOBAL,workspace_id.eq.{workspace_id}")
        else:
            # Only GLOBAL memories if no workspace is active
            query = query.eq("visibility", "GLOBAL")
            
        response = query.order("created_at", desc=True).limit(limit).execute()
        
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

def promote_memory(memory_id: str, user_id: str) -> bool:
    """Promotes a memory from temporary to permanent."""
    try:
        response = supabase.table("memory_items").update({
            "scope": "permanent",
            "expires_at": None
        }).eq("id", memory_id).eq("user_id", user_id).execute()
        return len(response.data) > 0
    except Exception as e:
        logger.error("Error promoting memory: %s", e, exc_info=True)
        return False

def get_memory_by_id(memory_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = supabase.table("memory_items").select("*").eq("id", memory_id).eq("user_id", user_id).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        logger.error("Error fetching memory %s: %s", memory_id, e, exc_info=True)
    return None
