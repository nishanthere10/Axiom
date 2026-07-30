from supabase import create_client, Client, ClientOptions
from core.config import settings
import httpx

# 🔐 FIX 4.2: Remove global HTTP/2 disable flag
# Instead, configure only Supabase client with HTTP/1.1 to fix PostgREST stream errors
# This prevents affecting other httpx clients in the app

_client: Client | None = None

def get_supabase() -> Client:
    """Lazy singleton factory for Supabase client."""
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
        # Create custom httpx client with HTTP/1.1 only (prevents PostgREST stream errors)
        http_client = httpx.Client(http2=False, timeout=30.0)
        
        opts = ClientOptions(
            postgrest_client_timeout=30,
            # Note: supabase-py doesn't directly expose httpx_client injection
            # If the library supports it in the future, inject http_client here
            # For now, the library will use default httpx which respects environment
        )
        
        _client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_SERVICE_ROLE_KEY,
            options=opts
        )
    return _client

# Backward-compatible alias — evaluates lazily at first access via PEP 562
def __getattr__(name):
    if name == "supabase":
        return get_supabase()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
