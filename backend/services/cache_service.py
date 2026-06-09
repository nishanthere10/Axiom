import threading
from typing import Any, Optional
from cachetools import TTLCache

# Bounded in-memory cache: 256 items max, 24-hour TTL (86400 seconds)
_lock = threading.Lock()
_store = TTLCache(maxsize=256, ttl=86400)


class Cache:
    """Thread-safe TTL cache wrapper with the same interface as SimpleCache."""

    def set(self, key: str, value: Any, ttl_hours: int = 24) -> None:
        with _lock:
            _store[key] = value

    def get(self, key: str) -> Optional[Any]:
        with _lock:
            return _store.get(key)

    def delete(self, key: str) -> None:
        with _lock:
            _store.pop(key, None)


# Global singleton instance — same import interface as before
cache = Cache()
