"""
Unit tests for Phase 3 Decision Knowledge & Memory Lifecycle Evolution.
"""
import pytest
import asyncio
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from agents.nodes.memory_relevance_evaluator import memory_relevance_evaluator, _parse_timestamp
from services.decision_memory_service import sync_decision_memory_status, generate_and_store_decision_memory

def test_parse_timestamp():
    # Fresh timestamp (0 days)
    now_iso = datetime.now(timezone.utc).isoformat()
    assert _parse_timestamp(now_iso) < 0.1

    # 10 days ago timestamp
    ten_days_ago = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    assert 9.5 < _parse_timestamp(ten_days_ago) < 10.5

    # Invalid timestamp
    assert _parse_timestamp("invalid") == 0.0
    assert _parse_timestamp(None) == 0.0


def test_memory_relevance_evaluator_pinned():
    state = {
        "retrieved_memories": [
            {
                "score": 0.5,
                "metadata": {"pinned": True, "title": "Pinned memory"}
            }
        ]
    }
    result = memory_relevance_evaluator(state)
    memories = result["retrieved_memories"]
    assert len(memories) == 1
    assert memories[0]["metadata"]["relevance_score"] == 1.0
    assert "Pinned" in memories[0]["metadata"]["relevance_reasoning"]


def test_memory_relevance_evaluator_status_weighting():
    state = {
        "retrieved_memories": [
            {
                "id": "mem_superseded",
                "score": 0.85,
                "metadata": {"decision_status": "SUPERSEDED", "title": "Old decision"}
            },
            {
                "id": "mem_accepted",
                "score": 0.80,
                "metadata": {"decision_status": "ACCEPTED", "title": "Accepted decision"}
            },
            {
                "id": "mem_rejected",
                "score": 0.90,
                "metadata": {"decision_status": "REJECTED", "title": "Rejected decision"}
            },
            {
                "id": "mem_dropped",
                "score": 0.40,
                "metadata": {"decision_status": "REJECTED", "title": "Irrelevant rejected decision"}
            }
        ]
    }

    result = memory_relevance_evaluator(state)
    memories = result["retrieved_memories"]

    # Accepted memory (0.80 * 1.2 = 0.96) should rank first
    # Superseded memory (0.85 * 0.3 = 0.255) should rank second
    # Rejected memory (0.90 * 0.1 = 0.09) should rank third
    # Dropped memory (0.40 * 0.1 = 0.04 < 0.05 floor) should be removed entirely
    assert len(memories) == 3
    assert memories[0]["id"] == "mem_accepted"
    assert memories[1]["id"] == "mem_superseded"
    assert memories[2]["id"] == "mem_rejected"
    assert memories[0]["metadata"]["relevance_score"] == 0.96


import asyncio

def test_sync_decision_memory_status():
    async def _test():
        with patch("services.decision_memory_service.get_supabase") as mock_get_supabase, \
             patch("services.decision_memory_service.update_memory_metadata") as mock_update_pinecone:
            
            mock_supabase = MagicMock()
            mock_get_supabase.return_value = mock_supabase

            # Mock existing memory row in Supabase
            mock_select = MagicMock()
            mock_select.execute.return_value.data = [
                {"id": "mem_123", "metadata": {"decision_status": "PROPOSED"}}
            ]
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value = mock_select

            success = await sync_decision_memory_status("dec_123", "SUPERSEDED", "user_123")

            assert success is True
            mock_supabase.table.return_value.update.assert_called()
            mock_update_pinecone.assert_called_with("mem_123", {"decision_status": "SUPERSEDED", "is_active": True})

    asyncio.run(_test())


def test_generate_and_store_decision_memory_upserts_pinecone():
    async def _test():
        with patch("services.decision_memory_service.get_supabase") as mock_get_supabase, \
             patch("services.decision_memory_service.generate_chat_completion") as mock_llm, \
             patch("services.decision_memory_service.create_memory_item") as mock_create_mem, \
             patch("services.decision_memory_service.upsert_memory") as mock_upsert:

            mock_supabase = MagicMock()
            mock_get_supabase.return_value = mock_supabase

            # Mock decision record and research report fetch
            mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
                {"id": "dec_1", "research_session_id": "sess_1", "title": "Test Title", "status": "APPROVED", "workspace_id": "ws_1"}
            ]
            mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
                {"question": "How to scale?", "recommendation_context": "Use Redis"}
            ]

            mock_llm.return_value.choices = [MagicMock(message=MagicMock(content="Summary text"))]
            mock_create_mem.return_value = {"id": "mem_generated", "created_at": "2026-07-22T00:00:00Z"}

            result = await generate_and_store_decision_memory("dec_1", "user_1")

            assert result is True
            mock_create_mem.assert_called_once()
            mock_upsert.assert_called_once()

    asyncio.run(_test())

