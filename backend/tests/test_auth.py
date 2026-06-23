import pytest
from fastapi import HTTPException
from unittest.mock import patch, MagicMock
from core.auth import get_current_user, verify_workspace_access

@pytest.mark.asyncio
async def test_get_current_user_no_token():
    mock_request = MagicMock()
    mock_request.headers.get.return_value = None
    with pytest.raises(HTTPException) as exc:
        await get_current_user(mock_request)
    assert exc.value.status_code == 401
    assert "Authorization header missing" in exc.value.detail

@pytest.mark.asyncio
async def test_get_current_user_invalid_format():
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "BearerTokenWithoutSpace"
    with pytest.raises(HTTPException) as exc:
        await get_current_user(mock_request)
    assert exc.value.status_code == 401

@pytest.mark.asyncio
@patch("core.auth.jwt")
@patch("core.auth.jwks_client")
async def test_get_current_user_valid(mock_jwks, mock_jwt):
    mock_request = MagicMock()
    mock_request.headers.get.return_value = "Bearer valid_token"
    
    mock_jwt.get_unverified_header.return_value = {"kid": "123"}
    mock_jwks.get_signing_key_from_jwt.return_value.key = "public_key"
    mock_jwt.decode.return_value = {"sub": "user_abc123"}
    
    user_id = await get_current_user(mock_request)
    assert user_id == "user_abc123"

@pytest.mark.asyncio
@patch("core.auth.get_supabase")
async def test_verify_workspace_access_fallback(mock_get_supabase):
    # Testing the fallback when workspace_id is not provided
    result = await verify_workspace_access(workspace_id=None, user_id="user123")
    assert result is None

@pytest.mark.asyncio
@patch("core.auth.get_supabase")
async def test_verify_workspace_access_success(mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    # Mock supabase response with data (meaning workspace found)
    mock_response = MagicMock()
    mock_response.data = [{"id": "ws_123"}]
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response
    
    result = await verify_workspace_access(workspace_id="ws_123", user_id="user123")
    assert result == "ws_123"

@pytest.mark.asyncio
@patch("core.auth.get_supabase")
async def test_verify_workspace_access_denied(mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    # Mock supabase response empty (workspace not found / access denied)
    mock_response = MagicMock()
    mock_response.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value.execute.return_value = mock_response
    
    with pytest.raises(HTTPException) as exc:
        await verify_workspace_access(workspace_id="ws_123", user_id="user123")
    assert exc.value.status_code == 403
