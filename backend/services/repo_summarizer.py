"""
Post-sync: generates a high-level architecture summary for a repository.
This summary is:
  1. Stored in github_repository_profiles.architecture_summary
  2. ALWAYS injected into research (not via similarity search — deterministic)
  3. Short (500 chars) — enough to ground the LLM without bloating the prompt

Called once after a full or incremental sync. Fire-and-forget.
"""
import logging
from typing import Optional
from services.llm_provider import generate_chat_completion
from services.db import get_supabase
from services.pinecone_service import get_pinecone_index

logger = logging.getLogger(__name__)


def generate_architecture_summary(
    repo_id: str,
    repo_name: str,
    workspace_id: Optional[str],
    user_id: str,
    indexed_file_count: int,
) -> None:
    """
    Samples indexed content from Pinecone (top 20 chunks) and asks the LLM
    to produce a ~400-word architecture summary. Stores in github_repository_profiles.
    """
    try:
        supabase = get_supabase()
        index = get_pinecone_index()
        if not index:
            return

        # Sample chunks from the repo using a neutral query vector
        from services.embedding_provider import generate_embedding
        sample_embedding = generate_embedding("system architecture components overview")
        if not sample_embedding:
            return

        results = index.query(
            vector=sample_embedding,
            top_k=20,
            include_metadata=True,
            filter={"user_id": {"$eq": user_id}, "repository": {"$eq": repo_name}},
        )

        chunks = []
        for match in results.get("matches", []):
            metadata = match.get("metadata", {})
            content = metadata.get("content", "")
            file_path = metadata.get("file_path", "")
            if content:
                chunks.append(f"[{file_path}]\n{content[:400]}")

        if not chunks:
            return

        prompt = f"""You are analyzing a software repository called '{repo_name}' with {indexed_file_count} indexed files.

Based on the following sampled content, produce a concise architecture summary:

{chr(10).join(chunks[:15])}

Write a structured summary (max 400 words) covering:
1. Primary purpose of this repository
2. Tech stack (languages, frameworks, databases, cloud services)
3. Key architectural patterns (microservices, event-driven, monolith, etc.)
4. Notable integrations or external dependencies
5. Any documented constraints or design decisions

Be specific and technical. Do not speculate. Only state what is evidenced in the content."""

        response = generate_chat_completion(
            [{"role": "user", "content": prompt}],
            model="openai/gpt-4o-mini",
            max_tokens=600,
            temperature=0.0,
        )
        summary = response.choices[0].message.content.strip()

        # Detect tech stack from content (simple keyword scan)
        tech_stack = _detect_tech_stack(chunks)

        # Upsert profile
        existing = supabase.table("github_repository_profiles").select("id").eq("repository_id", repo_id).execute()
        if existing.data:
            supabase.table("github_repository_profiles").update({
                "architecture_summary": summary,
                "tech_stack": tech_stack,
                "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
                "primary_language": tech_stack[0]["name"] if tech_stack else None,
            }).eq("repository_id", repo_id).execute()
        else:
            supabase.table("github_repository_profiles").insert({
                "repository_id":       repo_id,
                "workspace_id":        workspace_id,
                "architecture_summary": summary,
                "tech_stack":          tech_stack,
                "primary_language":    tech_stack[0]["name"] if tech_stack else None,
            }).execute()

        logger.info("Architecture summary generated for repo %s", repo_name)

    except Exception as e:
        logger.error("Failed to generate architecture summary for %s: %s", repo_name, e)


def _detect_tech_stack(chunks: list[str]) -> list[dict]:
    """Simple keyword scan to detect tech stack from indexed content."""
    TECH_KEYWORDS = {
        "FastAPI": "framework", "Django": "framework", "Flask": "framework",
        "Express": "framework", "Next.js": "framework", "React": "framework",
        "PostgreSQL": "database", "MySQL": "database", "MongoDB": "database",
        "Redis": "database", "Supabase": "database",
        "Pinecone": "vector_db", "Weaviate": "vector_db", "Qdrant": "vector_db",
        "LangChain": "ai", "LangGraph": "ai", "OpenAI": "ai",
        "AWS": "cloud", "GCP": "cloud", "Azure": "cloud", "Vercel": "cloud",
        "Docker": "infra", "Kubernetes": "infra", "Terraform": "infra",
        "TypeScript": "language", "Python": "language", "Go": "language",
        "Rust": "language", "Java": "language",
    }
    content_blob = " ".join(chunks).lower()
    found = []
    for name, category in TECH_KEYWORDS.items():
        if name.lower() in content_blob:
            count = content_blob.count(name.lower())
            found.append({"name": name, "category": category, "confidence": min(0.5 + count * 0.05, 1.0)})
    found.sort(key=lambda x: x["confidence"], reverse=True)
    return found[:15]
