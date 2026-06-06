from pinecone import Pinecone
from core.config import settings
from typing import List, Dict, Any, Optional

# Initialize Pinecone
pc = None
index = None

if settings.PINECONE_API_KEY:
    try:
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index_names = [i.name for i in pc.list_indexes()]
        if settings.PINECONE_INDEX in index_names:
            index = pc.Index(settings.PINECONE_INDEX)
        else:
            print(f"Warning: Pinecone index '{settings.PINECONE_INDEX}' not found. Available indexes: {index_names}")
    except Exception as e:
        print(f"Error initializing Pinecone: {e}")
        pc = None
        index = None
else:
    print("Warning: PINECONE_API_KEY not set. Memory system will not function.")

from services.embedding_provider import generate_embedding

def upsert_memory(memory_id: str, summary: str, metadata: Dict[str, Any]):
    """Upserts a memory into Pinecone."""
    print(f"[DEBUG: pinecone_service] upsert_memory called for memory_id={memory_id}")
    if not index:
        print("[DEBUG: pinecone_service] Pinecone index not initialized, skipping upsert.")
        return
        
    embedding = generate_embedding(summary)
    if not embedding:
        print("[DEBUG: pinecone_service] Failed to generate embedding, skipping upsert.")
        return
    
    # Store standard payload per spec
    payload = {
        "id": memory_id,
        "values": embedding,
        "metadata": metadata
    }
    
    try:
        index.upsert(vectors=[payload])
        print(f"[DEBUG: pinecone_service] Successfully upserted {memory_id} to Pinecone.")
        print("[DEBUG: pinecone_service] Pinecone upsert successful")
    except Exception as e:
        print(f"[DEBUG: pinecone_service] Error upserting to Pinecone: {e}")

def search_memories(query: str, top_k: int = 5, threshold: float = 0.70) -> List[Dict[str, Any]]:
    """Searches Pinecone for relevant memories above a similarity threshold."""
    print(f"[DEBUG: pinecone_service] search_memories called with query='{query}'")
    if not index:
        print("[DEBUG: pinecone_service] Pinecone index not initialized, returning empty search.")
        return []
        
    embedding = generate_embedding(query)
    if not embedding:
        print("[DEBUG: pinecone_service] embedding was None, returning empty search.")
        return []
    
    try:
        print("[DEBUG: pinecone_service] Querying pinecone index...")
        results = index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Filter by threshold
        valid_matches = []
        for match in results.get("matches", []):
            score = match.get("score", 0.0)
            print(f"[DEBUG: pinecone_service] Pinecone match found: id={match.get('id')} score={score}")
            if score >= threshold:
                valid_matches.append(match)
                
        print(f"[DEBUG: pinecone_service] Found {len(valid_matches)} matches above threshold {threshold}")
        print("[DEBUG: pinecone_service] Pinecone query successful")
        return valid_matches
    except Exception as e:
        print(f"[DEBUG: pinecone_service] Error querying Pinecone: {e}")
        return []
