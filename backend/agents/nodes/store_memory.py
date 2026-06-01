from typing import Dict, Any
from services.memory_service import create_memory_item
from services.pinecone_service import upsert_memory

def store_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Saves new memories to Postgres (source of truth) and Pinecone (vector search).
    """
    new_memories = state.get("new_memories", [])
    
    for memory_create in new_memories:
        # Save to Postgres
        pg_memory = create_memory_item(memory_create)
        
        if pg_memory:
            # Upsert to Pinecone if Postgres insert succeeded
            # Use the UUID assigned by Postgres
            memory_id = pg_memory["id"]
            
            # Pinecone payload
            metadata = memory_create.metadata
            metadata["memory_type"] = memory_create.memory_type
            metadata["created_at"] = pg_memory["created_at"]
            metadata["scope"] = memory_create.scope
            
            upsert_memory(
                memory_id=memory_id,
                summary=memory_create.summary,
                metadata=metadata
            )
            
    return {"status": "memory_stored"}
