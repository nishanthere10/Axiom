from services.cache_service import cache
from typing import Dict, Any

def get_cached_evidence(canonical_slug: str) -> list[Dict[str, Any]]:
    """Retrieves cached evidence for a topic if it exists and is not expired."""
    key = f"evidence_{canonical_slug}"
    return cache.get(key)

def set_cached_evidence(canonical_slug: str, evidence: list[Dict[str, Any]]) -> None:
    """Caches evidence for a topic for 24 hours."""
    key = f"evidence_{canonical_slug}"
    cache.set(key, evidence, ttl_hours=24)
