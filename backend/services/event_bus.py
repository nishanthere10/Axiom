"""
In-memory event bus for SSE streaming.

WARNING: This is an IN-PROCESS event bus. It does NOT work across multiple
uvicorn workers or multiple deployment instances. If you scale to >1 instance,
replace with Redis Pub/Sub or a similar cross-process message broker.

The background research task publishes progress events; SSE endpoints subscribe.
Uses asyncio.Queue per job_id — zero external dependencies (single-instance only).

Lifecycle:
  - Background task calls publish() after each LangGraph node.
  - SSE endpoint calls subscribe() on connection, unsubscribe() on disconnect.
  - Stale job entries are cleaned up by cleanup_stale_jobs() every 5 minutes.
"""
import asyncio
import logging
import time
from typing import Dict, List

logger = logging.getLogger(__name__)

# job_id → list of subscriber queues
_subscribers: Dict[str, List[asyncio.Queue]] = {}
# job_id → last activity timestamp (monotonic clock)
_last_activity: Dict[str, float] = {}

_JOB_TTL_SECONDS = 600  # 10 minutes


def subscribe(job_id: str) -> asyncio.Queue:
    """Register a new SSE subscriber for a job. Returns the queue to read from."""
    if job_id not in _subscribers:
        _subscribers[job_id] = []
    q: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers[job_id].append(q)
    _last_activity[job_id] = time.monotonic()
    logger.debug("SSE subscriber added for job_id=%s (total=%d)", job_id, len(_subscribers[job_id]))
    return q


def unsubscribe(job_id: str, queue: asyncio.Queue) -> None:
    """Remove a subscriber queue when the client disconnects."""
    if job_id in _subscribers:
        try:
            _subscribers[job_id].remove(queue)
        except ValueError:
            pass
        if not _subscribers[job_id]:
            _subscribers.pop(job_id, None)
            _last_activity.pop(job_id, None)
    logger.debug("SSE subscriber removed for job_id=%s", job_id)


async def publish(job_id: str, event: dict) -> None:
    """Publish an event to all subscribers of a job_id. Non-blocking."""
    _last_activity[job_id] = time.monotonic()
    queues = list(_subscribers.get(job_id, []))
    for q in queues:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("SSE queue full for job_id=%s — dropping event", job_id)


def cleanup_stale_jobs() -> None:
    """Remove job entries with no activity for longer than TTL. Call periodically."""
    cutoff = time.monotonic() - _JOB_TTL_SECONDS
    stale = [jid for jid, ts in list(_last_activity.items()) if ts < cutoff]
    for jid in stale:
        _subscribers.pop(jid, None)
        _last_activity.pop(jid, None)
    if stale:
        logger.info("EventBus: cleaned up %d stale job(s)", len(stale))
