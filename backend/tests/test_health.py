import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from services.health_service import check_postgres, check_pinecone, check_gemini, check_env_vars, run_all_checks

@pytest.mark.asyncio
@patch("services.health_service.get_supabase")
async def test_check_postgres_success(mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    # Mock successful query
    mock_supabase.table.return_value.select.return_value.limit.return_value.execute = MagicMock()
    
    result = await check_postgres()
    assert result is True

@pytest.mark.asyncio
@patch("services.health_service.get_supabase")
async def test_check_postgres_failure(mock_get_supabase):
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    # Mock exception during execution
    mock_supabase.table.return_value.select.return_value.limit.return_value.execute.side_effect = Exception("DB Down")
    
    result = await check_postgres()
    assert result is False

@pytest.mark.asyncio
@patch("services.health_service.settings")
@patch("httpx.AsyncClient")
async def test_check_gemini_success(mock_httpx, mock_settings):
    mock_settings.GEMINI_API_KEY = "test_key"
    
    mock_client = AsyncMock()
    mock_httpx.return_value.__aenter__.return_value = mock_client
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client.get.return_value = mock_response
    
    result = await check_gemini()
    assert result is True

@pytest.mark.asyncio
@patch("services.health_service.settings")
async def test_check_env_vars_missing(mock_settings):
    # Simulate missing env vars by mocking getattr to return None
    mock_settings.SUPABASE_URL = None
    
    result = await check_env_vars()
    assert result is False

@pytest.mark.asyncio
@patch("services.health_service.check_postgres", new_callable=AsyncMock)
@patch("services.health_service.check_pinecone", new_callable=AsyncMock)
@patch("services.health_service.check_gemini", new_callable=AsyncMock)
@patch("services.health_service.check_env_vars", new_callable=AsyncMock)
async def test_run_all_checks(mock_env, mock_gemini, mock_pinecone, mock_postgres):
    mock_postgres.return_value = True
    mock_pinecone.return_value = True
    mock_gemini.return_value = True
    mock_env.return_value = True
    
    result = await run_all_checks()
    assert result["status"] == "healthy"
    assert result["services"]["postgres"] is True
    assert result["services"]["pinecone"] is True
    assert result["services"]["gemini"] is True
    assert result["services"]["env_vars"] is True
