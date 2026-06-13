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

# Backward-compatible alias — evaluates lazily at first access via PEP 562
def __getattr__(name):
    if name == "supabase":
        return get_supabase()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
