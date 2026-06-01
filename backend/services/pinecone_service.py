from pinecone import Pinecone
import google.generativeai as genai
from core.config import settings
from typing import List, Dict, Any, Optional

# Initialize Pinecone
pc = None
index = None

if settings.PINECONE_API_KEY:
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
    # Check if index exists, if not it might fail but spec says user must create it
    if settings.PINECONE_INDEX in [i.name for i in pc.list_indexes()]:
        index = pc.Index(settings.PINECONE_INDEX)
    else:
        print(f"Warning: Pinecone index '{settings.PINECONE_INDEX}' not found.")
else:
    print("Warning: PINECONE_API_KEY not set.")

# Initialize Gemini for embeddings
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

def generate_embedding(text: str) -> List[float]:
    """Generates an embedding using Gemini text-embedding-004."""
    if not settings.GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not set, returning empty embedding.")
        return [0.0] * 768 # Fallback dummy embedding
        
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return [0.0] * 768

def upsert_memory(memory_id: str, summary: str, metadata: Dict[str, Any]):
    """Upserts a memory into Pinecone."""
    if not index:
        print("Pinecone index not initialized, skipping upsert.")
        return
        
    embedding = generate_embedding(summary)
    
    # Store standard payload per spec
    payload = {
        "id": memory_id,
        "values": embedding,
        "metadata": metadata
    }
    
    try:
        index.upsert(vectors=[payload])
    except Exception as e:
        print(f"Error upserting to Pinecone: {e}")

def search_memories(query: str, top_k: int = 5, threshold: float = 0.80) -> List[Dict[str, Any]]:
    """Searches Pinecone for relevant memories above a similarity threshold."""
    if not index:
        print("Pinecone index not initialized, returning empty search.")
        return []
        
    embedding = generate_embedding(query)
    
    try:
        results = index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # Filter by threshold
        valid_matches = []
        for match in results.get("matches", []):
            if match.get("score", 0.0) >= threshold:
                valid_matches.append(match)
                
        return valid_matches
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return []
