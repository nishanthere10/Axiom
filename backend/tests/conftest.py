import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
import json


# ─── Mock Supabase ────────────────────────────────────────────────────────
class FakeSupabaseTable:
    """In-memory mock for supabase.table(...).insert(...).execute() chains."""
    def __init__(self):
        self._store = {}  # table_name -> [rows]

    def table(self, name):
        if name not in self._store:
            self._store[name] = []
        self._current_table = name
        self._filters = {}
        return self

    def insert(self, data):
        if "id" not in data:
            import uuid
            data["id"] = str(uuid.uuid4())
        data.setdefault("created_at", "2026-01-01T00:00:00Z")
        self._store[self._current_table].append(data)
        self._insert_data = data
        return self

    def select(self, *args):
        return self

    def eq(self, field, value):
        self._filters[field] = value
        return self

    def order(self, *args, **kwargs):
        return self

    def limit(self, n):
        return self

    def range(self, start, end):
        return self

    def update(self, data):
        self._update_data = data
        return self

    def execute(self):
        result = MagicMock()
        if hasattr(self, "_insert_data"):
            result.data = [self._insert_data]
            del self._insert_data
        elif hasattr(self, "_update_data"):
            result.data = [self._update_data]
            del self._update_data
        else:
            # filter rows
            rows = self._store.get(self._current_table, [])
            for field, value in self._filters.items():
                rows = [r for r in rows if r.get(field) == value]
            result.data = rows
        return result


# ─── Fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def mock_supabase():
    fake = FakeSupabaseTable()
    with patch("services.db.supabase", fake):
        yield fake


@pytest.fixture
def mock_llm():
    """Patches generate_chat_completion to return deterministic JSON."""
    def _make_response(content_str: str):
        resp = MagicMock()
        resp.model = "test-model"
        resp.choices = [MagicMock()]
        resp.choices[0].message.content = content_str
        return resp

    with patch("services.llm_provider.generate_chat_completion") as mock:
        mock.side_effect = lambda messages, **kwargs: _make_response(json.dumps({
            "recommendation_context": "Use PostgreSQL for ACID compliance.",
            "tradeoffs": "- Pro: Strong consistency\n- Con: Harder to scale horizontally",
            "alternatives": "- MongoDB: Better for document-heavy workloads",
            "evidence_coverage": 0.8,
            "source_quality": 0.75,
            "contradiction_risk": 0.2,
            "decision_confidence": 0.85,
            "slug": "postgres-vs-mongodb",
            "evidence": [{"title": "PG Docs", "url": "https://pg.dev", "claim": "ACID", "trust_score": 0.9}],
            "consensus": "Strong Consensus",
        }))
        yield mock


@pytest.fixture
def mock_instructor():
    with patch("services.llm_provider.get_instructor_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_pinecone():
    # Patch get_pinecone_index to return None — this is what all callers check.
    # The module has no top-level `index` variable; it uses PineconeManager._index
    # accessed via get_pinecone_index().
    with patch("services.pinecone_service.get_pinecone_index", return_value=None):
        yield


@pytest.fixture
def mock_embedding():
    with patch("services.embedding_provider.generate_embedding") as mock:
        mock.return_value = [0.1] * 1024
        yield mock


@pytest.fixture
def mock_tavily():
    with patch("services.search_provider.search_tavily") as mock:
        mock.return_value = [
            {"title": "Test Source", "url": "https://example.com", "content": "Test content about PostgreSQL."}
        ]
        yield mock


@pytest.fixture
def mock_auth():
    """Patches get_current_user to always return a test user_id."""
    with patch("core.auth.get_current_user", return_value="test_user_123"):
        yield "test_user_123"


@pytest.fixture
def test_client(mock_supabase, mock_llm, mock_pinecone, mock_embedding, mock_tavily, mock_auth):
    """FastAPI TestClient with all external dependencies mocked."""
    from main import app
    from core.auth import get_current_user, verify_workspace_access, verify_workspace_path
    
    app.dependency_overrides[get_current_user] = lambda: "test_user_123"
    # verify_workspace_access reads the x-workspace-id header and does a DB lookup.
    # Override it to skip the DB check in all tests.
    app.dependency_overrides[verify_workspace_access] = lambda: None
    # verify_workspace_path is used by workspace-scoped routes (path parameter).
    # Return a fake workspace_id so workspace routes don't 403.
    app.dependency_overrides[verify_workspace_path] = lambda: "test_workspace_id"
    
    with TestClient(app) as client:
        yield client
        
    app.dependency_overrides = {}
