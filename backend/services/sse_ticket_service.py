"""
Short-lived SSE auth tickets.
EventSource does not support custom headers, so the JWT cannot be sent via
Authorization. Putting a long-lived JWT in a query param leaks it into server
access logs, CDN logs, and browser history.

Solution:
  1. Frontend calls POST /research/jobs/{id}/stream-ticket (normal Bearer auth).
  2. Server issues a 30-second, single-use token.
  3. Frontend passes token as ?ticket=... on the EventSource URL.
  4. Token is consumed on first use and discarded.

Tickets are stored in process memory — acceptable since they are transient and
the SSE connection opens within seconds of issuance.
"""
import secrets
import time
from typing import Dict, Optional, Tuple

# token → (user_id, job_id, expires_at_monotonic)
_tickets: Dict[str, Tuple[str, str, float]] = {}
_TICKET_TTL_SECONDS = 30


def issue_ticket(user_id: str, job_id: str) -> str:
    """Issue a single-use, 30-second SSE auth ticket. Returns the token string."""
    token = secrets.token_urlsafe(24)
    _tickets[token] = (user_id, job_id, time.monotonic() + _TICKET_TTL_SECONDS)
    return token


def peek_ticket(token: str) -> Optional[Tuple[str, str]]:
    """
    🔐 FIX 1.2: Validate ticket WITHOUT consuming it.
    Returns (user_id, job_id) on success, None if invalid or expired.
    Does NOT remove the ticket — use consume_ticket() after verification.
    """
    entry = _tickets.get(token)
    if entry is None:
        return None
    user_id, job_id, expires_at = entry
    if time.monotonic() > expires_at:
        return None
    return user_id, job_id


def consume_ticket(token: str) -> Optional[Tuple[str, str]]:
    """
    Validate and consume a ticket.
    Returns (user_id, job_id) on success, None if invalid or expired.
    The ticket is removed on first use regardless of outcome.
    """
    entry = _tickets.pop(token, None)
    if entry is None:
        return None
    user_id, job_id, expires_at = entry
    if time.monotonic() > expires_at:
        return None
    return user_id, job_id


def cleanup_expired() -> None:
    """Remove expired tickets. Call periodically to prevent memory growth."""
    now = time.monotonic()
    stale = [t for t, (_, _, exp) in list(_tickets.items()) if now > exp]
    for t in stale:
        _tickets.pop(t, None)
