import logging
from pinecone import Pinecone
from core.config import settings
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

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
            logger.warning("Pinecone index '%s' not found. Available indexes: %s", settings.PINECONE_INDEX, index_names)
    except Exception as e:
        logger.error("Error initializing Pinecone: %s", e, exc_info=True)
        pc = None
        index = None
else:
    logger.warning("PINECONE_API_KEY not set. Memory system will not function.")

from services.embedding_provider import generate_embedding

def upsert_memory(memory_id: str, summary: str, metadata: Dict[str, Any]):
    """Upserts a memory into Pinecone."""
    logger.debug("upsert_memory called for memory_id=%s", memory_id)
    if not index:
        logger.warning("Pinecone index not initialized, skipping upsert.")
        return
        
    embedding = generate_embedding(summary)
    if not embedding:
        logger.warning("Failed to generate embedding, skipping upsert.")
        return
    
    # Store standard payload per spec
    payload = {
        "id": memory_id,
        "values": embedding,
        "metadata": metadata
    }
    
    try:
        index.upsert(vectors=[payload])
        logger.debug("Successfully upserted %s to Pinecone.", memory_id)
    except Exception as e:
        logger.error("Error upserting to Pinecone: %s", e, exc_info=True)

def search_memories(query: str, user_id: str, top_k: int = 5, threshold: float = 0.70) -> List[Dict[str, Any]]:
    """Searches Pinecone for relevant memories above a similarity threshold."""
    logger.debug("search_memories called with query='%s'", query[:80])
    if not index:
        logger.warning("Pinecone index not initialized, returning empty search.")
        return []
        
    embedding = generate_embedding(query)
    if not embedding:
        logger.warning("Embedding was None, returning empty search.")
        return []
    
    try:
        logger.debug("Querying pinecone index...")
        results = index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
            filter={"user_id": {"$eq": user_id}}
        )
        
        # Filter by threshold
        valid_matches = []
        for match in results.get("matches", []):
            score = match.get("score", 0.0)
            logger.debug("Pinecone match found: id=%s score=%.3f", match.get('id'), score)
            if score >= threshold:
                valid_matches.append(match)
                
        logger.debug("Found %d matches above threshold %.2f", len(valid_matches), threshold)
        return valid_matches
    except Exception as e:
        logger.error("Error querying Pinecone: %s", e, exc_info=True)
        return []
