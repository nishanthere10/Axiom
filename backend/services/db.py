from supabase import create_client, Client, ClientOptions
from core.config import settings
import httpx
import threading
import asyncio
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# SECURITY FIX: Thread-safe Supabase client management
class SupabaseManager:
    """
    Thread-safe Supabase client manager with proper connection pooling.
    
    Prevents connection pool exhaustion and ensures thread safety
    across async contexts and background workers.
    """
    
    def __init__(self):
        self._clients: Dict[str, Client] = {}
        self._lock = threading.RLock()
        self._http_clients: Dict[str, httpx.Client] = {}
    
    def get_client(self, context: str = "default") -> Client:
        """
        Get or create a Supabase client for the given context.
        
        Args:
            context: Client context (e.g., 'api', 'worker', 'webhook')
                    Different contexts get separate connection pools.
        
        Returns:
            Thread-safe Supabase client instance
        """
        with self._lock:
            if context not in self._clients:
                self._clients[context] = self._create_client(context)
            return self._clients[context]
    
    def _create_client(self, context: str) -> Client:
        """Create a new Supabase client with proper configuration."""
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
        # SECURITY FIX: Create dedicated HTTP client with proper limits
        # Different contexts get different connection limits
        limits = self._get_connection_limits(context)
        
        http_client = httpx.Client(
            http2=False,  # Prevents PostgREST stream errors
            timeout=httpx.Timeout(30.0, connect=5.0),  # Separate connect timeout
            limits=httpx.Limits(
                max_keepalive_connections=limits["max_keepalive"],
                max_connections=limits["max_connections"],
                keepalive_expiry=30.0  # Close idle connections after 30s
            ),
            headers={
                "User-Agent": f"atlas-research/{context}",
                "Connection": "keep-alive"
            }
        )
        
        # Store HTTP client for cleanup
        self._http_clients[context] = http_client
        
        opts = ClientOptions(
            postgrest_client_timeout=30,
            storage_client_timeout=60,
            # Note: realtime_client_timeout not supported in this version
        )
        
        try:
            # SECURITY FIX: Proper client initialization with error handling
            client = create_client(
                settings.SUPABASE_URL, 
                settings.SUPABASE_SERVICE_ROLE_KEY,
                options=opts
            )
            
            # Inject our custom HTTP client if the library supports it
            # This is a best-effort approach since supabase-py API may vary
            if hasattr(client, '_client') and hasattr(client._client, 'session'):
                client._client.session = http_client
            elif hasattr(client, 'postgrest') and hasattr(client.postgrest, '_client'):
                client.postgrest._client.session = http_client
            
            logger.info(f"Created Supabase client for context: {context}")
            return client
            
        except Exception as e:
            # Clean up HTTP client on failure
            http_client.close()
            if context in self._http_clients:
                del self._http_clients[context]
            raise RuntimeError(f"Failed to create Supabase client for {context}: {e}")
    
    def _get_connection_limits(self, context: str) -> Dict[str, int]:
        """Get connection limits based on context."""
        limits = {
            "api": {"max_connections": 20, "max_keepalive": 10},
            "worker": {"max_connections": 10, "max_keepalive": 5},
            "webhook": {"max_connections": 5, "max_keepalive": 3},
            "default": {"max_connections": 15, "max_keepalive": 8},
        }
        return limits.get(context, limits["default"])
    
    def close_all(self):
        """Close all clients and HTTP connections. Call during app shutdown."""
        with self._lock:
            for context, http_client in self._http_clients.items():
                try:
                    http_client.close()
                    logger.info(f"Closed HTTP client for context: {context}")
                except Exception as e:
                    logger.warning(f"Error closing HTTP client {context}: {e}")
            
            self._clients.clear()
            self._http_clients.clear()
    
    def health_check(self) -> bool:
        """Perform basic health check on the default client."""
        try:
            client = self.get_client("health")
            # Simple query to test connectivity
            result = client.table("users").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False

# Global manager instance
_manager = SupabaseManager()

def get_supabase(context: str = "default") -> Client:
    """
    Get thread-safe Supabase client.
    
    SECURITY FIX: Now supports different contexts for better connection management.
    
    Args:
        context: Client context for connection pooling
                'api' - API request handlers
                'worker' - Background workers  
                'webhook' - Webhook handlers
                'default' - General purpose
    
    Returns:
        Thread-safe Supabase client
    """
    return _manager.get_client(context)

def close_supabase_connections():
    """Close all Supabase connections. Call during app shutdown."""
    global _manager
    _manager.close_all()

def supabase_health_check() -> bool:
    """Check if Supabase connection is healthy."""
    global _manager
    return _manager.health_check()

# Backward-compatible alias — evaluates lazily at first access via PEP 562
def __getattr__(name):
    if name == "supabase":
        return get_supabase("legacy")  # Use legacy context for backward compatibility
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
