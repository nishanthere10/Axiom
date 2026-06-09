import logging
import requests
from typing import List, Optional
from core.config import settings

logger = logging.getLogger(__name__)

class JinaEmbeddingProvider:
    def __init__(self):
        self.url = "https://api.jina.ai/v1/embeddings"
        self.model = "jina-embeddings-v5-text-small"
        self.expected_dimension = 1024

    def generate_embedding(self, text: str) -> Optional[List[float]]:
        logger.debug("Embedding generation started")
        
        api_key = settings.JINA_API_KEY
        if not api_key:
            logger.warning("JINA_API_KEY not set.")
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
                logger.error("Failed embedding request. Status: %d, Body: %s", response.status_code, response.text[:200])
                return None
                
            json_resp = response.json()
            if "data" not in json_resp or len(json_resp["data"]) == 0 or "embedding" not in json_resp["data"][0]:
                logger.error("Invalid embedding response format.")
                return None
                
            embedding = json_resp["data"][0]["embedding"]
            dimension = len(embedding)
            
            logger.debug("Embedding generation completed (dimension=%d)", dimension)
            
            if dimension != self.expected_dimension:
                logger.error("Vector dimension mismatch. Expected %d, got %d", self.expected_dimension, dimension)
                return None
                
            return embedding
            
        except Exception as e:
            logger.error("Error generating embedding: %s", e, exc_info=True)
            return None

# Singleton instance for easy import
provider = JinaEmbeddingProvider()

def generate_embedding(text: str) -> Optional[List[float]]:
    """Helper function to match previous interface"""
    return provider.generate_embedding(text)
