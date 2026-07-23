"""
Unit tests for Phase 4 Continuous Learning & Semantic Memory Deduplication.
"""
import pytest
from unittest.mock import patch, MagicMock
from api.schemas.memory import MemoryItemCreate
from services.memory_service import create_memory_item

def test_create_memory_item_exact_hash_dedup():
    with patch("services.memory_service.supabase") as mock_supabase:
        mock_select = MagicMock()
        mock_select.execute.return_value.data = [{"id": "existing_mem_1"}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value = mock_select

        item_data = MemoryItemCreate(
            memory_type="decision",
            source_id="src_1",
            source_type="decision_record",
            summary="Use PostgreSQL for database",
            user_id="user_1",
            workspace_id="ws_1"
        )

        res = create_memory_item(item_data)
        assert res is not None
        assert res.get("_dedup_skipped") is True
        assert res.get("id") == "existing_mem_1"


def test_create_memory_item_semantic_vector_dedup():
    with patch("services.memory_service.supabase") as mock_supabase, \
         patch("services.pinecone_service.search_memories") as mock_search:
        
        # No exact hash match
        mock_select = MagicMock()
        mock_select.execute.return_value.data = []
        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.eq.return_value = mock_select

        # Semantic vector search finds match with similarity > 0.90
        mock_search.return_value = [{"id": "semantic_dup_99", "score": 0.95}]

        item_data = MemoryItemCreate(
            memory_type="decision",
            source_id="src_2",
            source_type="decision_record",
            summary="Deploy PostgreSQL as primary storage engine",
            user_id="user_1",
            workspace_id="ws_1"
        )

        res = create_memory_item(item_data)
        assert res is not None
        assert res.get("_dedup_skipped") is True
        assert res.get("id") == "semantic_dup_99"
