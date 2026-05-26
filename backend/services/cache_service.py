from datetime import datetime, timedelta
from typing import Any, Optional

class SimpleCache:
    def __init__(self):
        self._store = {}

    def set(self, key: str, value: Any, ttl_hours: int = 24) -> None:
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        self._store[key] = {
            "data": value,
            "expires_at": expires_at
        }

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
            
        entry = self._store[key]
        if datetime.now() > entry["expires_at"]:
            del self._store[key]
            return None
            
        return entry["data"]

# Global singleton instance
cache = SimpleCache()
