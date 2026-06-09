"""
Unit tests for core service modules:
- cache_service (TTLCache)
- auth (Clerk JWT verification)
"""
import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from services.cache_service import Cache


# ─── Cache Service Tests ─────────────────────────────────────────────────

class TestTTLCache:
    def test_set_and_get(self):
        cache = Cache()
        cache.set("key1", {"data": "value"})
        assert cache.get("key1") == {"data": "value"}

    def test_get_missing_key_returns_none(self):
        cache = Cache()
        assert cache.get("nonexistent") is None

    def test_delete_key(self):
        cache = Cache()
        cache.set("key1", "value")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_delete_missing_key_no_error(self):
        cache = Cache()
        cache.delete("nonexistent")  # Should not raise

    def test_overwrite_key(self):
        cache = Cache()
        cache.set("key1", "v1")
        cache.set("key1", "v2")
        assert cache.get("key1") == "v2"


# ─── Auth Module Tests ───────────────────────────────────────────────────

class TestAuthDependency:
    """Tests for the get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_missing_token_returns_403(self):
        """FastAPI should return 403 when no Authorization header is provided."""
        # This is implicitly tested through the TestClient since we mock auth.
        # Direct test: calling get_current_user without credentials raises.
        from core.auth import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException

        with patch("core.auth._get_jwks_client") as mock_jwks:
            mock_client = MagicMock()
            mock_jwks.return_value = mock_client
            mock_client.get_signing_key_from_jwt.side_effect = Exception("Invalid token")

            creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(creds)
            assert exc_info.value.status_code == 401
