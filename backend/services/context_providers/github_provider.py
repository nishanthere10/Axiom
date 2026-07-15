import logging
import httpx
import base64
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Callable
from services.context_providers.base import ContextProvider
from services.clerk_service import get_github_oauth_token
from services.embedding_provider import generate_embedding
from services.pinecone_service import get_pinecone_index
from services.llm_provider import generate_chat_completion
from services.db import get_supabase
from services.code_extractor import should_index, extract_for_indexing
from services.gitignore_parser import GitignoreFilter
from tenacity import retry, stop_after_attempt, wait_exponential

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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
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

            pinecone_index = get_pinecone_index()
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
                        filter={"user_id": {"$eq": user_id}, "repository": {"$eq": resource_id}}
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
                        pinecone_index.upsert(vectors=batch)
                await asyncio.to_thread(do_upsert)
                    
            return len(vectors) > 0

        except Exception as e:
            logger.error(f"[GITHUB SYNC] Error syncing {resource_id}: {e}", exc_info=True)
            return False

    async def sync_incremental(
        self,
        user_id: str,
        repo_id: str,
        resource_id: str,
        workspace_id: Optional[str] = None,
        selected_paths: Optional[list[str]] = None,
        progress_callback: Optional[Callable] = None,
    ) -> dict:
        """
        Incremental sync: only re-index files whose SHA has changed.
        Returns a summary dict: { added, updated, deleted, skipped, total }.
        """
        import time as _time
        start = _time.time()
        supabase = get_supabase()
        parts = resource_id.split("/")
        if len(parts) != 2:
            return {"success": False, "error": "Invalid resource_id"}
        owner, repo = parts

        token = await self.get_token(user_id)
        if not token:
            return {"success": False, "error": "No GitHub token"}

        pinecone_index = get_pinecone_index()
        if not pinecone_index:
            return {"success": False, "error": "Pinecone unavailable"}

        # 1. Fetch current file tree with SHAs from GitHub
        headers = self._build_headers(token)
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(tree_url, headers=headers)
            if r.status_code != 200:
                return {"success": False, "error": f"GitHub tree API returned {r.status_code}"}
            tree_data = r.json()

        all_files = tree_data.get("tree", [])

        # 2. Fetch .gitignore from repo root
        gitignore_content = ""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                gi_url = f"https://api.github.com/repos/{owner}/{repo}/contents/.gitignore"
                gi_r = await client.get(gi_url, headers=headers)
                if gi_r.status_code == 200:
                    import base64 as _b64
                    gi_data = gi_r.json()
                    gitignore_content = _b64.b64decode(gi_data.get("content", "")).decode("utf-8", errors="replace")
        except Exception:
            pass
        gitignore = GitignoreFilter(gitignore_content)

        # 3. Filter files to index
        indexable = []
        for f in all_files:
            if f.get("type") != "blob":
                continue
            path = f["path"]
            size = f.get("size", 0)
            sha = f.get("sha", "")

            if gitignore.should_ignore(path):
                continue
            if not should_index(path, size):
                continue
            if selected_paths and not any(path.startswith(p) for p in selected_paths):
                continue

            indexable.append({"path": path, "sha": sha, "size": size})

        # 4. Load stored hashes
        repo_row = supabase.table("github_repositories").select(
            "file_hashes"
        ).eq("id", repo_id).execute()
        stored_hashes: dict[str, str] = (repo_row.data[0].get("file_hashes") or {}) if repo_row.data else {}

        # 5. Diff: what to add/update, what to delete
        current_paths = {f["path"] for f in indexable}
        to_process  = [f for f in indexable if stored_hashes.get(f["path"]) != f["sha"]]
        to_delete   = [p for p in stored_hashes if p not in current_paths]

        total = len(indexable)
        skipped = total - len(to_process)

        # 6. Delete removed files from Pinecone
        deleted_count = 0
        for path in to_delete:
            safe_path = path.replace("/", "_").replace(".", "_")
            vector_id = f"github_{user_id}_{owner}_{repo}_{safe_path}"
            try:
                def _del(vid=vector_id):
                    pinecone_index.delete(ids=[vid])
                await asyncio.to_thread(_del)
                deleted_count += 1
            except Exception as e:
                logger.warning("Failed to delete Pinecone vector for %s: %s", path, e)

        # 7. Re-index changed/new files (rate-aware batching)
        repo_metadata = await self.fetch_repo_metadata(token, owner, repo)
        sem = asyncio.Semaphore(3)   # max 3 concurrent GitHub API calls
        BATCH_SIZE = 50
        RATE_LIMIT_PAUSE = 1.0      # seconds between batches

        added_count = 0
        updated_count = 0
        new_hashes = dict(stored_hashes)
        for path in to_delete:
            new_hashes.pop(path, None)

        async def process_one(file_info: dict) -> Optional[dict]:
            path = file_info["path"]
            async with sem:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    r = await client.get(
                        f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                        headers=headers,
                    )
                    if r.status_code == 429:  # rate limited
                        retry_after = int(r.headers.get("Retry-After", "60"))
                        logger.warning("GitHub rate limited. Waiting %ds", retry_after)
                        await asyncio.sleep(retry_after)
                        return None
                    if r.status_code != 200:
                        return None

                    file_data = r.json()
                    import base64 as _b64
                    raw = _b64.b64decode(file_data.get("content", "")).decode("utf-8", errors="replace")

            indexable_text = extract_for_indexing(raw, path)
            if not indexable_text.strip():
                return {"discarded": True, "path": path, "sha": file_info["sha"]}

            # For code files: still run LLM summarization for context enrichment
            # For docs: summarize as before
            summary = await self.summarize(path, indexable_text, repo_metadata)

            embedding = await asyncio.to_thread(generate_embedding, summary)
            if not embedding:
                return {"discarded": True, "path": path, "sha": file_info["sha"]}

            safe_path = path.replace("/", "_").replace(".", "_")
            vector_id = f"github_{user_id}_{owner}_{repo}_{safe_path}"

            from pathlib import Path as _P
            ext = _P(path).suffix.lower().lstrip(".")

            metadata = {
                "user_id":       user_id,
                "workspace_id":  workspace_id or "",
                "provider":      "github",
                "repository":    resource_id,
                "file_path":     path,
                "document_type": "code" if ext not in {"md", "mdx", "txt", "rst"} else "markdown",
                "language":      ext,
                "content":       summary[:8000],
                "raw_snippet":   raw[:500],
            }
            return {"id": vector_id, "values": embedding, "metadata": metadata, "path": path, "sha": file_info["sha"], "is_new": path not in stored_hashes}

        # Process in batches
        vectors = []
        for i in range(0, len(to_process), BATCH_SIZE):
            batch = to_process[i:i + BATCH_SIZE]
            results = await asyncio.gather(*[process_one(f) for f in batch])
            for res in results:
                if res:
                    if res.get("discarded"):
                        new_hashes[res["path"]] = res["sha"]
                        continue
                    vectors.append(res)
                    if res.get("is_new"):
                        added_count += 1
                    else:
                        updated_count += 1
                    new_hashes[res["path"]] = res["sha"]
                    if progress_callback:
                        if asyncio.iscoroutinefunction(progress_callback):
                            await progress_callback(res["path"])
                        else:
                            progress_callback(res["path"])
            if i + BATCH_SIZE < len(to_process):
                await asyncio.sleep(RATE_LIMIT_PAUSE)

        # 8. Batch upsert to Pinecone
        if vectors:
            pinecone_vectors = [{"id": v["id"], "values": v["values"], "metadata": v["metadata"]} for v in vectors]
            def _upsert():
                for j in range(0, len(pinecone_vectors), 100):
                    pinecone_index.upsert(vectors=pinecone_vectors[j:j + 100])
            await asyncio.to_thread(_upsert)

        # 9. Update stored hashes and sync metadata
        duration_ms = int((_time.time() - start) * 1000)
        supabase.table("github_repositories").update({
            "file_hashes":       new_hashes,
            "last_sync_at":      __import__("datetime").datetime.utcnow().isoformat(),
            "indexed_file_count": len(new_hashes),
            "total_file_count":   len(indexable),
        }).eq("id", repo_id).execute()

        # 10. Log sync
        supabase.table("github_sync_log").insert({
            "repository_id": repo_id,
            "user_id":       user_id,
            "trigger":       "manual",
            "files_added":   added_count,
            "files_updated": updated_count,
            "files_deleted": deleted_count,
            "files_total":   total,
            "duration_ms":   duration_ms,
            "success":       True,
        }).execute()

        from services.repo_summarizer import generate_architecture_summary
        import threading
        threading.Thread(
            target=generate_architecture_summary,
            args=(repo_id, resource_id, workspace_id, user_id, len(new_hashes)),
            daemon=True,
        ).start()

        return {
            "success": True,
            "added":   added_count,
            "updated": updated_count,
            "deleted": deleted_count,
            "skipped": skipped,
            "total":   total,
        }

    async def retrieve(self, query: str, user_id: str, scope: Optional[str] = None, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        pinecone_index = get_pinecone_index()
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
            if workspace_id:
                filter_dict["workspace_id"] = {"$eq": workspace_id}
            if scope:
                filter_dict["repository"] = {"$eq": scope}

            def do_query():
                return pinecone_index.query(
                    vector=query_embedding,
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
