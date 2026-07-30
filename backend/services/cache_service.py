import threading
from typing import Any, Optional
from cachetools import TTLCache

# 🔐 FIX 3.3: Add Prometheus metrics for cache observability
try:
    from prometheus_client import Counter, Gauge
    cache_hits = Counter('cache_hits_total', 'Total cache hits')
    cache_misses = Counter('cache_misses_total', 'Total cache misses')
    cache_size = Gauge('cache_size_items', 'Current number of items in cache')
    METRICS_ENABLED = True
except ImportError:
    # prometheus_client not installed, disable metrics
    METRICS_ENABLED = False

# Bounded in-memory cache: 1024 items max, 24-hour TTL (86400 seconds)
_lock = threading.Lock()
_store = TTLCache(maxsize=1024, ttl=86400)


class Cache:
    """Thread-safe TTL cache wrapper with Prometheus metrics."""

    def set(self, key: str, value: Any, ttl_hours: int = 24) -> None:
        with _lock:
            _store[key] = value
            if METRICS_ENABLED:
                cache_size.set(len(_store))

    def get(self, key: str) -> Optional[Any]:
        with _lock:
            value = _store.get(key)
            if METRICS_ENABLED:
                if value is not None:
                    cache_hits.inc()
                else:
                    cache_misses.inc()
            return value

    def delete(self, key: str) -> None:
        with _lock:
            _store.pop(key, None)
            if METRICS_ENABLED:
                cache_size.set(len(_store))


# Global singleton instance — same import interface as before
cache = Cache()
