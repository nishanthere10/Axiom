import asyncio
import logging
from typing import Dict, Any

from services.db import get_supabase
from services.pinecone_service import search_memories
from services.search_provider import search_tavily
import litellm

logger = logging.getLogger(__name__)

async def check_postgres() -> bool:
    try:
        # Run synchronous supabase call in thread pool to avoid blocking async loop
        supabase = get_supabase()
        await asyncio.to_thread(supabase.table("users").select("id").limit(1).execute)
        return True
    except Exception as e:
        logger.warning(f"Postgres health check failed: {e}")
        return False

async def check_pinecone() -> bool:
    try:
        # search_memories is synchronous, wrap in to_thread
        await asyncio.to_thread(search_memories, query="health_check_ping", user_id="system", top_k=1)
        return True
    except Exception as e:
        logger.warning(f"Pinecone health check failed: {e}")
        return False

async def check_groq() -> bool:
    try:
        # We can use litellm.acompletion for async execution
        await litellm.acompletion(
            model="groq/llama-3.3-70b-versatile", 
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1
        )
        return True
    except Exception as e:
        logger.warning(f"Groq health check failed: {e}")
        return False

async def check_tavily() -> bool:
    try:
        # search_tavily is synchronous and expects a list of queries
        await asyncio.to_thread(search_tavily, queries=["health check ping"])
        return True
    except Exception as e:
        logger.warning(f"Tavily health check failed: {e}")
        return False

async def _run_with_timeout(coro, timeout: float = 2.0) -> bool:
    try:
        return await asyncio.wait_for(coro(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.warning(f"Health check {coro.__name__} timed out after {timeout}s")
        return False
    except Exception as e:
        logger.warning(f"Health check {coro.__name__} raised exception: {e}")
        return False

async def run_all_checks() -> Dict[str, Any]:
    """
    Runs all health checks concurrently with strict timeouts.
    Returns a status dict: {"postgres": True, "pinecone": False, ...}
    """
    results = await asyncio.gather(
        _run_with_timeout(check_postgres),
        _run_with_timeout(check_pinecone),
        _run_with_timeout(check_groq),
        _run_with_timeout(check_tavily),
        return_exceptions=True
    )
    
    # gather returns exceptions if any escaped _run_with_timeout
    safe_results = [r if isinstance(r, bool) else False for r in results]
    
    services = {
        "postgres": safe_results[0],
        "pinecone": safe_results[1],
        "groq": safe_results[2],
        "tavily": safe_results[3]
    }
    
    status = "healthy" if all(services.values()) else "degraded"
    
    return {
        "status": status,
        "services": services
    }
