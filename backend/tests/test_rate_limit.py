import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.mark.skip(reason="Endpoint deprecated — /research returns 410 Gone intentionally. Rate limit test needs workspace-scoped route.")
def test_rate_limit_exceeded(test_client, mock_auth, mock_supabase, mock_llm):
    # The /research endpoint has a rate limit of 5/minute
    # Mock verify_workspace_access so it doesn't fail
    from unittest.mock import patch
    
    with patch("core.auth.verify_workspace_access", return_value="ws_123"):
        # Make 6 requests
        for i in range(5):
            response = test_client.post("/research", json={"question": f"Test {i}"}, headers={"x-workspace-id": "ws_123"})
            # The first 5 should succeed (status 202)
            assert response.status_code == 202

        # The 6th request should hit the rate limit
        response = test_client.post("/research", json={"question": "Test 6"}, headers={"x-workspace-id": "ws_123"})
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.text
