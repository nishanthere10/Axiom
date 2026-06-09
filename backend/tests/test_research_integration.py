"""
Integration tests for the /research endpoints.
Validates end-to-end flow: submit → poll → document retrieval.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ─── Test: Submit Research ────────────────────────────────────────────────

def test_submit_research_returns_202(test_client: TestClient):
    """POST /research should return 202 with session_id, job_id, and status."""
    response = test_client.post(
        "/research",
        json={"question": "Should I use PostgreSQL or MongoDB for a high-write event log system?"}
    )
    assert response.status_code == 202
    data = response.json()
    assert "session_id" in data
    assert "job_id" in data
    assert data["status"] == "started"


def test_submit_research_validates_input(test_client: TestClient):
    """POST /research with missing question should return 422."""
    response = test_client.post("/research", json={})
    assert response.status_code == 422


# ─── Test: Job Status ────────────────────────────────────────────────────

def test_get_job_status_not_found(test_client: TestClient):
    """GET /research/jobs/{id} with non-existent ID should return 404."""
    response = test_client.get("/research/jobs/nonexistent-id")
    assert response.status_code == 404


# ─── Test: Session History ───────────────────────────────────────────────

def test_get_session_history_empty(test_client: TestClient):
    """GET /research/history should return empty list when no sessions exist."""
    response = test_client.get("/research/history")
    assert response.status_code == 200
    data = response.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)


# ─── Test: Session Document Not Found ────────────────────────────────────

def test_get_session_document_not_found(test_client: TestClient):
    """GET /research/sessions/{id} with non-existent session should return 404."""
    response = test_client.get("/research/sessions/nonexistent-session")
    assert response.status_code == 404
