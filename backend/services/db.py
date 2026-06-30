from supabase import create_client, Client, ClientOptions
from core.config import settings
import os

# Force HTTP/1.1 on httpx globally to prevent HTTP/2 stream disconnects (RemoteProtocolError)
# This is a known robust workaround for Supabase/PostgREST connection drops
os.environ["HTTPX_DEFAULT_HTTP2"] = "false"

_client: Client | None = None

def get_supabase() -> Client:
    """Lazy singleton factory for Supabase client."""
    global _client
    if _client is None:
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
        # Increase timeouts and pass connection options
        opts = ClientOptions(postgrest_client_timeout=30)
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
