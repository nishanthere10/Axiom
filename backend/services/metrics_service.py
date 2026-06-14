import logging
from services.db import get_supabase

logger = logging.getLogger(__name__)

def emit_event(event_type: str, metadata: dict = None, user_id: str = None):
    """
    Appends a new event to the analytics_events table.
    This should be fire-and-forget and never crash the main request.
    """
    if metadata is None:
        metadata = {}
        
    try:
        supabase = get_supabase()
        supabase.table("analytics_events").insert({
            "event_type": event_type,
            "user_id": user_id,
            "metadata": metadata
        }).execute()
    except Exception as e:
        logger.warning(f"Failed to emit analytics event {event_type}: {e}")

def emit_research_completed(user_id: str, latency_ms: int, confidence: float, evidence_count: int, sources_used: int):
    emit_event("research_completed", {
        "latency_ms": latency_ms,
        "confidence": confidence,
        "evidence_count": evidence_count,
        "sources_used": sources_used
    }, user_id=user_id)

def emit_comparison_completed(user_id: str, latency_ms: int, confidence: float):
    emit_event("comparison_completed", {
        "latency_ms": latency_ms,
        "confidence": confidence
    }, user_id=user_id)

def emit_memory_retrieved(user_id: str, retrieved_count: int, used_count: int, latency_ms: int, hit: bool):
    emit_event("memory_retrieved", {
        "retrieved_count": retrieved_count,
        "used_count": used_count,
        "latency_ms": latency_ms,
        "hit": hit
    }, user_id=user_id)

def emit_export_requested(user_id: str, export_type: str, latency_ms: int):
    emit_event("export_requested", {
        "export_type": export_type,
        "latency_ms": latency_ms
    }, user_id=user_id)

def emit_provider_event(provider: str, event: str, latency_ms: int):
    # event should be 'success', 'failure', or 'fallback'
    emit_event("provider_event", {
        "provider": provider,
        "event": event,
        "latency_ms": latency_ms
    })

def emit_memory_job_failed():
    emit_event("memory_job_failed", {})
