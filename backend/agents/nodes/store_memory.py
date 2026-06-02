from typing import Dict, Any
from services.memory_service import create_memory_item
from services.pinecone_service import upsert_memory

def store_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Saves new memories to Postgres (source of truth) and Pinecone (vector search).
    """
    print("[DEBUG: Node] -> store_memory starting...")
    new_memories = state.get("new_memories", [])
    
    if not new_memories:
        print("[DEBUG: store_memory] No new_memories to store.")
        return {"status": "memory_stored"}
        
    for memory_create in new_memories:
        try:
            print(f"[DEBUG: store_memory] Saving to Postgres (source_id={memory_create.source_id})...")
            # Save to Postgres
            pg_memory = create_memory_item(memory_create)
            
            if pg_memory:
                print(f"[DEBUG: store_memory] Saved to Postgres (id={pg_memory['id']}). Upserting to Pinecone...")
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
            else:
                print("[DEBUG: store_memory] Postgres insert failed, skipping Pinecone.")
        except Exception as e:
            print(f"[DEBUG: store_memory] Error storing memory: {e}")
            
    print("[DEBUG: store_memory] Finished storing memories.")
    return {"status": "memory_stored"}
