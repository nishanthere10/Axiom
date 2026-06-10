from supabase import create_client, Client
from core.config import settings

_client: Client | None = None

def get_supabase() -> Client:
    """Lazy singleton factory for Supabase client."""
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    return _client

# Backward-compatible alias — existing code using `from services.db import supabase` still works.
# This evaluates lazily at first access via the module-level property pattern.
supabase = get_supabase()
