import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock
import hmac
import hashlib
import json

client = TestClient(app)

@pytest.fixture
def mock_supabase():
    with patch("api.routes.webhooks.get_supabase") as mock_get:
        mock_db = MagicMock()
        mock_get.return_value = mock_db
        yield mock_db

def test_github_webhook_push_ping(mock_supabase):
    response = client.post(
        "/webhooks/github/push",
        headers={"X-GitHub-Event": "ping"},
        json={}
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True

def test_github_webhook_push_missing_secret(mock_supabase):
    mock_res = MagicMock()
    mock_res.data = [{"id": "r1", "user_id": "u1", "webhook_secret": "", "workspace_id": "w1"}]
    mock_supabase.table().select().eq().eq().eq().execute.return_value = mock_res

    response = client.post(
        "/webhooks/github/push",
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": "fake_sig"},
        json={"repository": {"full_name": "owner/repo"}}
    )
    assert response.status_code == 403
    assert "missing webhook_secret" in response.json()["error"]

def test_github_webhook_push_invalid_signature(mock_supabase):
    mock_res = MagicMock()
    mock_res.data = [{"id": "r1", "user_id": "u1", "webhook_secret": "mysecret", "workspace_id": "w1"}]
    mock_supabase.table().select().eq().eq().eq().execute.return_value = mock_res

    response = client.post(
        "/webhooks/github/push",
        headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": "sha256=fakesig"},
        content=b'{"repository": {"full_name": "owner/repo"}}'
    )
    assert response.status_code == 401
    assert response.json()["error"] == "Invalid signature"

def test_github_webhook_push_valid_signature(mock_supabase):
    mock_res = MagicMock()
    mock_res.data = [{"id": "r1", "user_id": "u1", "webhook_secret": "mysecret", "workspace_id": "w1"}]
    mock_supabase.table().select().eq().eq().eq().execute.return_value = mock_res

    body_bytes = b'{"repository": {"full_name": "owner/repo"}}'
    mac = hmac.new(b"mysecret", body_bytes, hashlib.sha256)
    valid_sig = "sha256=" + mac.hexdigest()

    # The background task is executed via fastapi's test client automatically, 
    # but we can patch github_provider.sync_incremental to prevent actual sync.
    with patch("services.context_providers.github_provider.github_provider.sync_incremental") as mock_sync:
        response = client.post(
            "/webhooks/github/push",
            headers={"X-GitHub-Event": "push", "X-Hub-Signature-256": valid_sig},
            content=body_bytes
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        mock_sync.assert_called_once()
