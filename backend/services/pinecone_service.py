import logging
from pinecone import Pinecone
from core.config import settings
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

# Initialize Pinecone
pc = None
index = None

if settings.PINECONE_API_KEY:
    try:
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        # Create the index object locally (doesn't make a blocking network call on import)
        index = pc.Index(settings.PINECONE_INDEX)
    except Exception as e:
        logger.error("Error initializing Pinecone: %s", e, exc_info=True)
        pc = None
        index = None
else:
    logger.warning("PINECONE_API_KEY not set. Memory system will not function.")

from services.embedding_provider import generate_embedding

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def upsert_memory(memory_id: str, summary: str, metadata: Dict[str, Any], workspace_id: Optional[str] = None):
    """Upserts a memory into Pinecone. Retries on transient failures."""
    logger.debug("upsert_memory called for memory_id=%s", memory_id)
    if not index:
        logger.warning("Pinecone index not initialized, skipping upsert.")
        return
        
    embedding = generate_embedding(summary)
    if not embedding:
        logger.warning("Failed to generate embedding, skipping upsert.")
        return
    
    
    # Store standard payload per spec
    pinecone_metadata = metadata.copy()
    if workspace_id:
        pinecone_metadata["workspace_id"] = workspace_id
        
    payload = {
        "id": memory_id,
        "values": embedding,
        "metadata": pinecone_metadata
    }
    
    try:
        index.upsert(vectors=[payload])
        logger.debug("Successfully upserted %s to Pinecone.", memory_id)
    except Exception as e:
        logger.error("Error upserting to Pinecone: %s", e, exc_info=True)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def search_memories(query: str, user_id: str, workspace_id: Optional[str] = None, top_k: int = 5, threshold: float = 0.70) -> List[Dict[str, Any]]:
    """Searches Pinecone for relevant memories above a similarity threshold. Retries on transient failures."""
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
        filter_dict = {"user_id": {"$eq": user_id}}
        if workspace_id:
            # Matches GLOBAL memories (no workspace_id) OR WORKSPACE memories
            # Pinecone metadata filtering doesn't natively support OR across fields easily without complex syntax,
            # so we'll filter by user_id and then in Python we'll prefer the workspace ones if they overlap.
            # Actually, to be safe, we just get top K for the user, and filter manually if we need to.
            # But the spec says: Metadata Filtering: {"workspace_id": "...", "scope": "..."}
            # For Pinecone $in or $or:
            filter_dict = {
                "user_id": {"$eq": user_id},
                "$or": [
                    {"workspace_id": {"$exists": False}},
                    {"workspace_id": {"$eq": workspace_id}}
                ]
            }
        else:
            filter_dict = {
                "user_id": {"$eq": user_id},
                "workspace_id": {"$exists": False}
            }

        results = index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
            filter=filter_dict
        )
        
        # Filter by threshold
        valid_matches = []
        for match in results.get("matches", []):
            match_dict = match.to_dict() if hasattr(match, "to_dict") else dict(match)
            score = match_dict.get("score", 0.0)
            logger.debug("Pinecone match found: id=%s score=%.3f", match_dict.get('id'), score)
            if score >= threshold:
                valid_matches.append(match_dict)
                
        logger.debug("Found %d matches above threshold %.2f", len(valid_matches), threshold)
        return valid_matches
    except Exception as e:
        logger.error("Error querying Pinecone: %s", e, exc_info=True)
        return []
