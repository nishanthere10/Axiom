import logging
from typing import Dict, Any
from services.memory_service import create_memory_item
from services.pinecone_service import upsert_memory

logger = logging.getLogger(__name__)

def store_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Saves new memories to Postgres (source of truth) and Pinecone (vector search).
    Non-critical node — keeps graceful degradation.
    """
    logger.debug("Node -> store_memory starting...")
    new_memories = state.get("new_memories", [])
    
    if not new_memories:
        logger.debug("No new_memories to store.")
        return {"status": "memory_stored"}
        
    warnings = state.get("warnings", [])
    failed_count = 0
    
    for memory_create in new_memories:
        try:
            logger.debug("Saving to Postgres (source_id=%s)...", memory_create.source_id)
            # Save to Postgres
            pg_memory = create_memory_item(memory_create)
            
            if pg_memory:
                logger.debug("Saved to Postgres (id=%s). Upserting to Pinecone...", pg_memory['id'])
                # Upsert to Pinecone if Postgres insert succeeded
                # Use the UUID assigned by Postgres
                memory_id = pg_memory["id"]
                
                # Pinecone payload
                metadata = memory_create.metadata.copy() if memory_create.metadata else {}
                metadata["memory_type"] = memory_create.memory_type
                metadata["created_at"] = pg_memory["created_at"]
                metadata["scope"] = memory_create.scope
                metadata["user_id"] = memory_create.user_id  # CRITICAL: search_memories filters by this
                
                upsert_memory(
                    memory_id=memory_id,
                    # Use richer embed_text if create_memory built one (question + summary + constraints).
                    # Falls back to summary for backward compat with memories created before this change.
                    summary=metadata.pop("embed_text", None) or memory_create.summary,
                    metadata=metadata
                )
            else:
                logger.warning("Postgres insert failed, skipping Pinecone.")
                failed_count += 1
        except Exception as e:
            logger.warning("Error storing memory (non-fatal): %s", e)
            failed_count += 1
    
    if failed_count > 0:
        warnings.append(f"⚠️ Memory storage failed for {failed_count} item(s) — this decision may not be remembered for future sessions.")
            
    logger.debug("Finished storing memories.")
    return {"status": "memory_stored", "warnings": warnings}
