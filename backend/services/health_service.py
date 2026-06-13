import asyncio
import logging
from typing import Dict, Any

from services.db import get_supabase

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
        from services.pinecone_service import index
        if not index:
            logger.warning("Pinecone health check failed: index not initialized")
            return False
        # Lightweight connectivity probe — no embedding generation, no user filtering
        await asyncio.to_thread(index.describe_index_stats)
        return True
    except Exception as e:
        logger.warning(f"Pinecone health check failed: {e}")
        return False

async def _run_with_timeout(coro, timeout: float = 5.0) -> bool:
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
    Only checks infrastructure dependencies (Postgres, Pinecone).
    Groq and Tavily are excluded because health-checking them burns
    API credits and rate limits on every poll cycle.
    """
    results = await asyncio.gather(
        _run_with_timeout(check_postgres),
        _run_with_timeout(check_pinecone),
        return_exceptions=True
    )
    
    # gather returns exceptions if any escaped _run_with_timeout
    safe_results = [r if isinstance(r, bool) else False for r in results]
    
    services = {
        "postgres": safe_results[0],
        "pinecone": safe_results[1],
    }
    
    status = "healthy" if all(services.values()) else "degraded"
    
    return {
        "status": status,
        "services": services
    }
