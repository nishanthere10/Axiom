import os
from services.embedding_provider import generate_embedding
from services.pinecone_service import upsert_memory, search_memories

def test_embedding_generation():
    print("--- Testing Embedding Generation ---")
    text = "What is the best OS for ethical hacking?"
    embedding = generate_embedding(text)
    
    if embedding is None:
        print("Test Failed: generate_embedding returned None. (Is JINA_API_KEY set?)")
        return False
        
    dim = len(embedding)
    print(f"Embedding generated with dimension: {dim}")
    if dim != 1024:
        print(f"Test Failed: Expected dimension 1024, got {dim}")
        return False
        
    print("Test Passed: Embedding generation succeeds and dimension == 1024")
    return embedding

def test_pinecone_flow():
    print("\n--- Testing Pinecone Flow ---")
    
    # 1. Test Upsert
    memory_id = "test-memory-1"
    summary = "Kali Linux and Parrot OS are the top OS choices for ethical hacking."
    metadata = {"source": "test", "type": "decision"}
    
    try:
        upsert_memory(memory_id, summary, metadata)
        print("Pinecone upsert executed.")
    except Exception as e:
        print(f"Test Failed: Upsert raised exception {e}")
        return False
        
    # 2. Test Retrieval
    try:
        query = "Which OS should I use for ethical hacking?"
        results = search_memories(query, top_k=1, threshold=0.5)
        
        print(f"Pinecone retrieval executed. Found {len(results)} results.")
        # We don't strictly assert length > 0 because Pinecone takes a moment to index
        # but the query should not crash.
    except Exception as e:
        print(f"Test Failed: Retrieval raised exception {e}")
        return False
        
    print("Test Passed: Pinecone flow completed without exceptions.")
    return True

if __name__ == "__main__":
    emb = test_embedding_generation()
    if emb:
        test_pinecone_flow()
