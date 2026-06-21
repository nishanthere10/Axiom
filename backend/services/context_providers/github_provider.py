import logging
import httpx
import base64
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Callable
from services.context_providers.base import ContextProvider
from services.clerk_service import get_github_oauth_token
from services.embedding_provider import generate_embedding
from services.pinecone_service import index as pinecone_index
from services.llm_provider import generate_chat_completion

logger = logging.getLogger(__name__)

# Max .md files to index per repo to avoid rate limits / token overload
MAX_MD_FILES = 50
# Max chars per file before truncating for the LLM
MAX_FILE_CHARS = 15000


class GitHubProvider(ContextProvider):
    def __init__(self):
        pass

    async def get_token(self, user_id: str) -> str | None:
        return await get_github_oauth_token(user_id)

    def _build_headers(self, token: str) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    async def get_file_tree(self, token: str, owner: str, repo: str) -> Dict[str, Any]:
        """Returns .md files grouped by top-level folder."""
        headers = self._build_headers(token)
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.get(tree_url, headers=headers)
                if r.status_code != 200:
                    return {"folders": [], "total_count": 0}
                
                tree_data = r.json()
                all_files = tree_data.get("tree", [])
                
                md_paths = [
                    f["path"] for f in all_files
                    if f.get("type") == "blob"
                    and f["path"].lower().endswith(".md")
                    and not any(skip in f["path"] for skip in ["node_modules", "vendor", ".github/workflows"])
                ]
                
                # Group by top-level folder
                folders_map = {}
                for path in md_paths:
                    parts = path.split("/")
                    folder = parts[0] if len(parts) > 1 else "root"
                    if folder not in folders_map:
                        folders_map[folder] = []
                    folders_map[folder].append(path)
                
                folders_list = []
                for folder, files in folders_map.items():
                    folders_list.append({
                        "name": folder,
                        "files": files,
                        "count": len(files)
                    })
                
                return {
                    "folders": sorted(folders_list, key=lambda x: x["name"]),
                    "total_count": len(md_paths)
                }
        except Exception as e:
            logger.error(f"[GITHUB TREE] Error: {e}")
            return {"folders": [], "total_count": 0}

    async def fetch_markdown_files(
        self, token: str, owner: str, repo: str, 
        selected_folders: Optional[List[str]] = None,
        prefetched_paths: Optional[List[str]] = None
    ) -> List[Tuple[str, str]]:
        """
        Discover and fetch .md files in the repository.
        Filters by selected_folders if provided.
        Skips tree API call if prefetched_paths is provided.
        """
        headers = self._build_headers(token)
        md_files: List[Tuple[str, str]] = []

        async with httpx.AsyncClient(timeout=30.0) as client:
            if prefetched_paths is not None:
                md_paths = prefetched_paths
            else:
                # Step 1: Get the full file tree (recursive)
                tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
                try:
                    r = await client.get(tree_url, headers=headers)
                    if r.status_code != 200:
                        return []

                    tree_data = r.json()
                    all_files = tree_data.get("tree", [])

                    md_paths = [
                        f["path"] for f in all_files
                        if f.get("type") == "blob"
                        and f["path"].lower().endswith(".md")
                        and not any(skip in f["path"] for skip in ["node_modules", "vendor", ".github/workflows"])
                    ]
                except Exception as e:
                    logger.error(f"[GITHUB SYNC] Error fetching file tree: {e}")
                    return []

            # Step 2: Filter by selected folders
            if selected_folders and len(selected_folders) > 0:
                filtered_paths = []
                for path in md_paths:
                    folder = path.split("/")[0] if "/" in path else "root"
                    if folder in selected_folders:
                        filtered_paths.append(path)
                md_paths = filtered_paths

            if len(md_paths) > MAX_MD_FILES:
                logger.warning(f"[GITHUB SYNC] Capping to {MAX_MD_FILES} files (found {len(md_paths)})")
                md_paths = md_paths[:MAX_MD_FILES]

            # Step 3: Fetch each .md file (Sequential to avoid GitHub secondary rate limits)
            for path in md_paths:
                file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
                try:
                    r = await client.get(file_url, headers=headers)
                    if r.status_code != 200:
                        continue

                    file_data = r.json()
                    encoding = file_data.get("encoding", "")

                    if encoding == "base64":
                        content = base64.b64decode(file_data.get("content", "")).decode("utf-8", errors="replace")
                    else:
                        content = file_data.get("content", "")

                    if content.strip():
                        md_files.append((path, content))
                except Exception as e:
                    logger.warning(f"[GITHUB SYNC] Failed to fetch {path}: {e}")

        return md_files

    async def fetch_repo_metadata(self, token: str, owner: str, repo: str) -> str:
        headers = self._build_headers(token)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
                if r.status_code == 200:
                    data = r.json()
                    return (
                        f"Repository: {owner}/{repo}\n"
                        f"Description: {data.get('description', 'N/A')}\n"
                        f"Primary Language: {data.get('language', 'N/A')}\n"
                        f"Topics: {', '.join(data.get('topics', []))}\n"
                    )
        except Exception:
            pass
        return f"Repository: {owner}/{repo}\n"

    async def summarize(self, file_path: str, raw_content: str, repo_metadata: str) -> str:
        prompt = (
            f"PART 1: Identity header\n"
            f"You are summarizing file `{file_path}` from the repository.\n"
            f"This file is a Markdown documentation file. Do NOT summarize source code.\n"
            f"Repository context:\n{repo_metadata}\n\n"
            f"PART 2: Structured extraction\n"
            f"Extract the following into a dense, objective, searchable summary:\n"
            f"- PURPOSE: What is this file for? (1 sentence)\n"
            f"- COMPONENTS: Key components, services, or modules described.\n"
            f"- STACK: Frameworks, databases, cloud providers, APIs mentioned.\n"
            f"- ARCHITECTURE: Decisions, patterns, constraints, or design principles documented.\n"
            f"- INTEGRATIONS: External APIs, services, or third-party dependencies noted.\n"
            f"- CONSTRAINTS: Any hard rules, limitations, or warnings documented.\n\n"
            f"PART 3: Relevance tags\n"
            f"End the summary with:\n"
            f"RELEVANT FOR: [comma-separated list of topics/questions this file would be useful for]\n"
            f"Example: RELEVANT FOR: database choice, authentication architecture, deployment strategy\n\n"
            f"Do not include conversational filler. Be dense and specific.\n\n"
            f"File Content:\n{raw_content[:MAX_FILE_CHARS]}"
        )
        try:
            messages = [{"role": "system", "content": prompt}]
            # generate_chat_completion is synchronous, run in thread to avoid blocking event loop
            response = await asyncio.to_thread(
                generate_chat_completion, 
                messages, 
                model="nvidia/nemotron-3-ultra-550b-a55b"
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"[GITHUB SYNC] Failed to summarize {file_path}: {e}")
            return raw_content[:500]

    async def sync(self, user_id: str, resource_id: str, selected_folders: Optional[List[str]] = None, progress_callback: Optional[Callable] = None, prefetched_paths: Optional[List[str]] = None) -> bool:
        """
        Sync all .md files from a GitHub repository with parallel LLM summarization.
        """
        try:
            parts = resource_id.split("/")
            if len(parts) != 2:
                return False
            owner, repo = parts

            token = await self.get_token(user_id)
            if not token:
                return False

            if not pinecone_index:
                return False

            repo_metadata = await self.fetch_repo_metadata(token, owner, repo)

            # Discover and fetch .md files (filtered by selected_folders or prefetched_paths)
            md_files = await self.fetch_markdown_files(token, owner, repo, selected_folders, prefetched_paths)
            if not md_files:
                return False

            # Delete all existing vectors for this repo before re-syncing
            try:
                def delete_old():
                    pinecone_index.delete(
                        filter={"user_id": {"$eq": user_id}, "repository": {"$eq": resource_id}},
                        namespace=user_id
                    )
                await asyncio.to_thread(delete_old)
            except Exception:
                pass

            # Parallel Processing Pipeline
            sem = asyncio.Semaphore(3) # Limit to 3 concurrent LLM calls

            async def process_file(file_path: str, file_content: str):
                async with sem:
                    summary = await self.summarize(file_path, file_content, repo_metadata)
                
                # generate_embedding is synchronous, run in thread
                embedding = await asyncio.to_thread(generate_embedding, summary)
                if not embedding:
                    return None

                safe_path = file_path.replace("/", "_").replace(".", "_")
                vector_id = f"github_{user_id}_{owner}_{repo}_{safe_path}"

                metadata = {
                    "user_id": user_id,
                    "provider": "github",
                    "repository": resource_id,
                    "file_path": file_path,
                    "document_type": "markdown",
                    "content": summary[:8000],
                    "raw_snippet": file_content[:1000]
                }
                return {"id": vector_id, "values": embedding, "metadata": metadata}

            tasks = [process_file(p, c) for p, c in md_files]
            vectors = []
            
            for coro in asyncio.as_completed(tasks):
                res = await coro
                if res:
                    vectors.append(res)
                    if progress_callback:
                        file_path = res["metadata"]["file_path"]
                        # Call sync or async callback
                        if asyncio.iscoroutinefunction(progress_callback):
                            await progress_callback(file_path)
                        else:
                            progress_callback(file_path)

            if vectors:
                # Batch upsert to Pinecone
                def do_upsert():
                    for i in range(0, len(vectors), 100):
                        batch = vectors[i:i+100]
                        pinecone_index.upsert(vectors=batch, namespace=user_id)
                await asyncio.to_thread(do_upsert)
                    
            return len(vectors) > 0

        except Exception as e:
            logger.error(f"[GITHUB SYNC] Error syncing {resource_id}: {e}", exc_info=True)
            return False

    async def retrieve(self, query: str, user_id: str, scope: Optional[str] = None) -> List[Dict[str, Any]]:
        if not pinecone_index:
            return []

        try:
            query_embedding = await asyncio.to_thread(generate_embedding, query)
            if not query_embedding:
                return []

            filter_dict: Dict[str, Any] = {
                "user_id": {"$eq": user_id},
                "provider": {"$eq": "github"}
            }
            if scope:
                filter_dict["repository"] = {"$eq": scope}

            def do_query():
                return pinecone_index.query(
                    vector=query_embedding,
                    namespace=user_id,
                    top_k=8,
                    include_metadata=True,
                    filter=filter_dict
                )
            results = await asyncio.to_thread(do_query)

            chunks = []
            for match in results.get("matches", []):
                score = match.get("score", 0.0)
                if score >= 0.35:
                    metadata = match.get("metadata", {})
                    chunks.append({
                        "id": match.get("id"),
                        "score": score,
                        "repository": metadata.get("repository", "unknown"),
                        "file_path": metadata.get("file_path", "unknown"),
                        "content": metadata.get("content", ""),
                        "raw_snippet": metadata.get("raw_snippet", "")
                    })

            return chunks

        except Exception as e:
            logger.error(f"[GITHUB RETRIEVE] Error: {e}")
            return []

github_provider = GitHubProvider()
