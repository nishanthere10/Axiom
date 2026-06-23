import pytest
from unittest.mock import patch, MagicMock
from tenacity import RetryError

@pytest.mark.asyncio
async def test_github_file_tree_retry():
    # We want to test that get_file_tree retries on failure
    from services.context_providers.github_provider import github_provider
    import httpx
    
    with patch("httpx.AsyncClient.get") as mock_get:
        # Mock it to fail 2 times, then succeed
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"tree": []}
        
        mock_get.side_effect = [
            httpx.RequestError("Network error 1"),
            httpx.RequestError("Network error 2"),
            mock_response
        ]
        
        result = await github_provider.get_file_tree("fake_token", "owner", "repo")
        assert result == {"folders": [], "total_count": 0}
        assert mock_get.call_count == 3

@pytest.mark.asyncio
async def test_github_file_tree_retry_failure():
    from services.context_providers.github_provider import github_provider
    import httpx
    
    with patch("httpx.AsyncClient.get") as mock_get:
        # Mock it to fail 4 times (which exceeds the stop_after_attempt(3))
        mock_get.side_effect = [
            httpx.RequestError("Network error 1"),
            httpx.RequestError("Network error 2"),
            httpx.RequestError("Network error 3"),
            httpx.RequestError("Network error 4"),
        ]
        
        # Tenacity will raise RetryError if it exhausts attempts
        with pytest.raises(RetryError) as exc:
            await github_provider.get_file_tree("fake_token", "owner", "repo")
        
        assert mock_get.call_count == 3  # stop_after_attempt(3)
