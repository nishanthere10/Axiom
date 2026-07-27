"""
In-memory or Redis event bus for SSE streaming.

If REDIS_URL is configured in settings, this uses Redis Pub/Sub to broadcast events
across multiple uvicorn workers. If not, it falls back to an in-memory asyncio.Queue,
which only works for a single instance.

Lifecycle:
  - Background task calls publish() after each LangGraph node.
  - SSE endpoint calls subscribe() on connection, unsubscribe() on disconnect.
  - Stale job entries are cleaned up by cleanup_stale_jobs() every 5 minutes.
"""
import asyncio
import logging
import time
import json
from typing import Dict, List
from core.config import settings

logger = logging.getLogger(__name__)

# Redis Client Singleton
_redis_client = None

def _get_redis():
    global _redis_client
    if _redis_client is None and settings.REDIS_URL:
        import redis.asyncio as redis
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client

# In-Memory State (used if Redis is disabled OR for managing local queues when Redis is enabled)
_subscribers: Dict[str, List[asyncio.Queue]] = {}
_last_activity: Dict[str, float] = {}
_JOB_TTL_SECONDS = 600

# Redis background listener tasks
_redis_listeners: Dict[str, asyncio.Task] = {}

async def _redis_listener_task(job_id: str):
    """Background task to listen to Redis and push to local queues."""
    redis_client = _get_redis()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(job_id)
    logger.debug("Redis PubSub listener started for job_id=%s", job_id)
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                data = json.loads(message["data"])
                _last_activity[job_id] = time.monotonic()
                queues = list(_subscribers.get(job_id, []))
                for q in queues:
                    try:
                        q.put_nowait(data)
                    except asyncio.QueueFull:
                        pass
    except asyncio.CancelledError:
        logger.debug("Redis PubSub listener cancelled for job_id=%s", job_id)
        try:
            await pubsub.unsubscribe(job_id)
            await pubsub.close()
        except Exception:
            pass
    except Exception as e:
        logger.error("Redis listener error for %s: %s", job_id, e)

def subscribe(job_id: str) -> asyncio.Queue:
    """Register a new SSE subscriber for a job. Returns the queue to read from."""
    if job_id not in _subscribers:
        _subscribers[job_id] = []
        
        # If Redis is enabled, start a listener for this job_id
        if _get_redis() and job_id not in _redis_listeners:
            _redis_listeners[job_id] = asyncio.create_task(_redis_listener_task(job_id))
            
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
            # Cancel Redis listener if active
            task = _redis_listeners.pop(job_id, None)
            if task:
                task.cancel()
    logger.debug("SSE subscriber removed for job_id=%s", job_id)

async def publish(job_id: str, event: dict) -> None:
    """Publish an event to all subscribers of a job_id. Non-blocking."""
    _last_activity[job_id] = time.monotonic()
    redis_client = _get_redis()
    
    if redis_client:
        try:
            await redis_client.publish(job_id, json.dumps(event))
        except Exception as e:
            logger.error("Redis publish failed for job_id=%s: %s. Falling back to memory bus.", job_id, e)
            _publish_local(job_id, event)
    else:
        _publish_local(job_id, event)

def _publish_local(job_id: str, event: dict):
    queues = list(_subscribers.get(job_id, []))
    for q in queues:
        try:
            q.put_nowait(event)
        except asyncio.QueueFull:
            logger.warning("SSE queue full for job_id=%s — dropping event", job_id)

async def close() -> None:
    """Close Redis connection cleanly during shutdown."""
    global _redis_client
    if _redis_client:
        try:
            await _redis_client.aclose()
        except AttributeError:
            await _redis_client.close()
        except Exception as e:
            logger.error("Error closing Redis client: %s", e)
        _redis_client = None

def cleanup_stale_jobs() -> None:
    """Remove job entries with no activity for longer than TTL. Call periodically."""
    cutoff = time.monotonic() - _JOB_TTL_SECONDS
    stale = [jid for jid, ts in list(_last_activity.items()) if ts < cutoff]
    for jid in stale:
        _subscribers.pop(jid, None)
        _last_activity.pop(jid, None)
        task = _redis_listeners.pop(jid, None)
        if task:
            task.cancel()
    if stale:
        logger.info("EventBus: cleaned up %d stale job(s)", len(stale))
