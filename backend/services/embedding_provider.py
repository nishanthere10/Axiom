import requests
from typing import List, Optional
from core.config import settings

class JinaEmbeddingProvider:
    def __init__(self):
        self.url = "https://api.jina.ai/v1/embeddings"
        self.model = "jina-embeddings-v5-text-small"
        self.expected_dimension = 1024

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        print("[DEBUG: embedding_provider] Embedding generation started")
        
        api_key = settings.JINA_API_KEY
        if not api_key:
            print("[DEBUG: embedding_provider] Warning: JINA_API_KEY not set.")
            return None
            
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": self.model,
            "input": [text]
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=data)
            
            if response.status_code != 200:
                print(f"[DEBUG: embedding_provider] Failed embedding request. Status: {response.status_code}, Body: {response.text}")
                return None
                
            json_resp = response.json()
            if "data" not in json_resp or len(json_resp["data"]) == 0 or "embedding" not in json_resp["data"][0]:
                print("[DEBUG: embedding_provider] Invalid embedding response format.")
                return None
                
            embedding = json_resp["data"][0]["embedding"]
            dimension = len(embedding)
            
            print("[DEBUG: embedding_provider] Embedding generation completed")
            print(f"[DEBUG: embedding_provider] Embedding dimension returned: {dimension}")
            
            if dimension != self.expected_dimension:
                print(f"[DEBUG: embedding_provider] Error: Vector dimension mismatch. Expected {self.expected_dimension}, got {dimension}")
                return None
                
            return embedding
            
        except Exception as e:
            print(f"[DEBUG: embedding_provider] Error generating embedding: {e}")
            return None

# Singleton instance for easy import
provider = JinaEmbeddingProvider()

def generate_embedding(text: str) -> Optional[List[float]]:
    """Helper function to match previous interface"""
    return provider.generate_embedding(text)
