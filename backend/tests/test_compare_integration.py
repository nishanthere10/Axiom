"""
Integration tests for the /compare endpoints.
Validates comparison submission, retrieval, and save flows.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ─── Test: Submit Comparison ─────────────────────────────────────────────

def test_submit_comparison_same_session_returns_400(test_client: TestClient):
    """POST /compare with identical session IDs should return 400."""
    response = test_client.post(
        "/compare",
        json={"session_a": "same-id", "session_b": "same-id"}
    )
    assert response.status_code == 400
    assert "Cannot compare a session with itself" in response.json()["detail"]


# ─── Test: Get Comparison Not Found ──────────────────────────────────────

def test_get_comparison_not_found(test_client: TestClient):
    """GET /compare/{id} with non-existent ID should return 404."""
    response = test_client.get("/compare/nonexistent-id")
    assert response.status_code == 404


# ─── Test: Get Saved Comparisons ─────────────────────────────────────────

def test_get_saved_comparisons_empty(test_client: TestClient):
    """GET /compare/saved should return empty list when no saved comparisons exist."""
    response = test_client.get("/compare/saved")
    assert response.status_code == 200
    data = response.json()
    assert "comparisons" in data
    assert isinstance(data["comparisons"], list)
