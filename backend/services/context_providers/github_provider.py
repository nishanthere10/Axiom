import logging
import httpx
from typing import Dict, Any, List, Optional
from services.context_providers.base import ContextProvider
from services.clerk_service import get_github_oauth_token
from services.embedding_provider import get_embedding_provider
from services.pinecone_service import index as pinecone_index
from services.llm_provider import generate_chat_completion
from core.config import settings
import uuid

logger = logging.getLogger(__name__)

class GitHubProvider(ContextProvider):
    def __init__(self):
        self.embedding_provider = get_embedding_provider()
        
    async def get_token(self, user_id: str) -> str | None:
        return await get_github_oauth_token(user_id)

    async def fetch_repo_contents(self, token: str, repo_owner: str, repo_name: str) -> str:
        """
        Fetch README and minimal documentation files. We strictly DO NOT fetch source code.
        """
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        raw_text = ""
        
        async with httpx.AsyncClient() as client:
            # Fetch README
            try:
                readme_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/readme"
                r = await client.get(readme_url, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    import base64
                    content = base64.b64decode(data.get("content", "")).decode("utf-8")
                    raw_text += f"# README\\n\\n{content}\\n\\n"
            except Exception as e:
                logger.warning(f"Failed to fetch README for {repo_owner}/{repo_name}: {e}")

            # Fetch Repo details (description, topics, language)
            try:
                repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
                r = await client.get(repo_url, headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    raw_text += f"# Repository Metadata\\nDescription: {data.get('description', '')}\\n"
                    raw_text += f"Language: {data.get('language', '')}\\n"
                    raw_text += f"Topics: {', '.join(data.get('topics', []))}\\n\\n"
            except Exception as e:
                logger.warning(f"Failed to fetch metadata for {repo_owner}/{repo_name}: {e}")

        return raw_text

    async def summarize(self, raw_data: str) -> str:
        """
        Condense raw github data into a clean architectural/engineering context summary.
        """
        prompt = (
            "You are an expert software architect analyzing a repository's documentation.\\n"
            "Extract the following into a dense, objective summary:\\n"
            "- The primary purpose of the repository.\\n"
            "- The technology stack (languages, frameworks, databases).\\n"
            "- The architectural patterns used.\\n"
            "- Infrastructure/Deployment methods mentioned.\\n"
            "Do not output conversational filler. Output only the objective technical summary.\\n\\n"
            f"Raw Documentation:\\n{raw_data[:20000]}" # Limit to 20k chars
        )
        try:
            messages = [{"role": "system", "content": prompt}]
            # Fast, cheap model for summarization
            response = generate_chat_completion(messages, model="groq/llama-3.1-8b-instant")
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Failed to summarize GitHub repo: {e}")
            # Fallback to truncated raw data
            return raw_data[:1000]

    async def sync(self, user_id: str, resource_id: str) -> bool:
        """
        Sync a specific GitHub repository.
        resource_id should be in format 'owner/repo_name'
        """
        try:
            parts = resource_id.split("/")
            if len(parts) != 2:
                logger.error(f"Invalid resource_id format: {resource_id}")
                return False
            owner, repo = parts

            token = await self.get_token(user_id)
            if not token:
                logger.error(f"No GitHub OAuth token found for user {user_id}")
                return False

            raw_data = await self.fetch_repo_contents(token, owner, repo)
            if not raw_data.strip():
                logger.warning(f"No data fetched for {resource_id}")
                return False

            summary = await self.summarize(raw_data)

            # Embed the summary
            embedding = self.embedding_provider.embed_query(summary)

            # Upsert to Pinecone
            vector_id = f"github_{user_id}_{owner}_{repo}"
            metadata = {
                "user_id": user_id,
                "provider": "github",
                "repository": resource_id,
                "document_type": "summary",
                "content": summary
            }
            
            pinecone_index.upsert(
                vectors=[{
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                }],
                namespace=user_id
            )
            logger.info(f"Successfully synced GitHub repository {resource_id} for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error syncing GitHub repository {resource_id} for user {user_id}: {e}", exc_info=True)
            return False

    async def retrieve(self, query: str, user_id: str, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant GitHub chunks. We use Pinecone direct vector search.
        """
        try:
            query_embedding = self.embedding_provider.embed_query(query)
            
            filter_dict = {
                "user_id": {"$eq": user_id},
                "provider": {"$eq": "github"}
            }
            if scope: # e.g. "atlas-backend"
                filter_dict["repository"] = {"$eq": scope}
                
            results = pinecone_index.query(
                vector=query_embedding,
                namespace=user_id,
                top_k=5,
                include_metadata=True,
                filter=filter_dict
            )
            
            chunks = []
            for match in results.get("matches", []):
                if match.get("score", 0.0) >= 0.5: # basic relevance threshold
                    metadata = match.get("metadata", {})
                    chunks.append({
                        "id": match.get("id"),
                        "score": match.get("score"),
                        "repository": metadata.get("repository", "unknown"),
                        "content": metadata.get("content", "")
                    })
            return chunks
        except Exception as e:
            logger.error(f"Error retrieving GitHub context: {e}")
            return []

github_provider = GitHubProvider()
