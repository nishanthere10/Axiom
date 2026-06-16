from abc import ABC, abstractmethod
from typing import Dict, Any, List

class ContextProvider(ABC):
    """
    Base interface for all Context Providers (GitHub, Notion, Jira, etc.)
    Ensures a standard contract for syncing and retrieving external context.
    """
    
    @abstractmethod
    async def sync(self, user_id: str, resource_id: str) -> bool:
        """
        Synchronize data from the provider to Pinecone.
        Fetches, summarizes, embeds, and stores the context.
        """
        pass
        
    @abstractmethod
    async def summarize(self, raw_data: str) -> str:
        """
        Condense raw provider data into a dense summary.
        """
        pass
        
    @abstractmethod
    async def retrieve(self, query: str, user_id: str, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context chunks for a given query.
        """
        pass
