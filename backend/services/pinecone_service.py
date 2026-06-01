from pinecone import Pinecone
import google.generativeai as genai
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

# Initialize Gemini for embeddings
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

def generate_embedding(text: str) -> Optional[List[float]]:
    """Generates an embedding using Gemini text-embedding-004."""
    if not settings.GEMINI_API_KEY:
        print("Warning: GEMINI_API_KEY not set.")
        return None
        
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type="retrieval_document"
        )
        return result['embedding']
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return None

def upsert_memory(memory_id: str, summary: str, metadata: Dict[str, Any]):
    """Upserts a memory into Pinecone."""
    if not index:
        print("Pinecone index not initialized, skipping upsert.")
        return
        
    embedding = generate_embedding(summary)
    if not embedding:
        print("Failed to generate embedding, skipping upsert.")
        return
    
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
    if not embedding:
        return []
    
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
