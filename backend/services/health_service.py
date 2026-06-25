import asyncio
import logging
from typing import Dict, Any

from core.config import settings
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

async def check_gemini() -> bool:
    try:
        if not settings.GEMINI_API_KEY:
            logger.warning("Gemini health check failed: GEMINI_API_KEY not set")
            return False
            
        # Use a lightweight HTTP GET to verify the API key without consuming LLM generation credits
        import httpx
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={settings.GEMINI_API_KEY}"
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return True
            else:
                logger.warning(f"Gemini health check failed with status {response.status_code}")
                return False
    except Exception as e:
        logger.warning(f"Gemini health check failed: {e}")
        return False

async def check_env_vars() -> bool:
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "GEMINI_API_KEY",
        "PINECONE_API_KEY",
        "CLERK_SECRET_KEY"
    ]
    missing = [v for v in required_vars if not getattr(settings, v, None)]
    if missing:
        logger.warning(f"Env vars health check failed. Missing: {missing}")
        return False
    return True

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
    """
    results = await asyncio.gather(
        _run_with_timeout(check_postgres),
        _run_with_timeout(check_pinecone),
        _run_with_timeout(check_gemini),
        _run_with_timeout(check_env_vars),
        return_exceptions=True
    )
    
    safe_results = [r if isinstance(r, bool) else False for r in results]
    
    services = {
        "postgres": safe_results[0],
        "pinecone": safe_results[1],
        "gemini": safe_results[2],
        "env_vars": safe_results[3],
    }
    
    status = "healthy" if all(services.values()) else "degraded"
    
    return {
        "status": status,
        "services": services
    }
