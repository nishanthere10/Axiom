import os
import logging
import json
import base64
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.config import settings
from services.db import get_supabase

logger = logging.getLogger(__name__)

security = HTTPBearer()

# ──────────────────────────────────────────────────────────
# JWKS Client — Lazy singleton with multiple discovery paths
# ──────────────────────────────────────────────────────────
_jwks_client: PyJWKClient | None = None


def _resolve_jwks_url() -> str:
    """
    Tries multiple strategies to find the JWKS URL:
      1. Explicit CLERK_JWKS_URL env var (highest priority)
      2. Derived from CLERK_JWT_ISSUER + /.well-known/jwks.json
      3. Derived from NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY (pk_test_... → domain)
    """
    # Strategy 1: Direct JWKS URL (env var or settings)
    explicit = os.getenv("CLERK_JWKS_URL") or settings.CLERK_JWKS_URL
    if explicit:
        logger.info("AUTH: Using explicit CLERK_JWKS_URL = %s", explicit)
        return explicit

    # Strategy 2: Derive from issuer
    issuer = settings.CLERK_JWT_ISSUER
    if issuer:
        url = f"{issuer.rstrip('/')}/.well-known/jwks.json"
        logger.info("AUTH: Derived JWKS URL from CLERK_JWT_ISSUER = %s", url)
        return url

    # Strategy 3: Derive from Clerk publishable key
    pk = os.getenv("NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "")
    if pk.startswith("pk_"):
        try:
            # Publishable key format: pk_test_<base64-encoded-domain>
            encoded_part = pk.split("_", 2)[2]  # everything after pk_test_ or pk_live_
            # Pad base64 if needed
            padded = encoded_part + "=" * (-len(encoded_part) % 4)
            domain = base64.b64decode(padded).decode("utf-8").rstrip("$")
            url = f"https://{domain}/.well-known/jwks.json"
            logger.info("AUTH: Derived JWKS URL from publishable key = %s", url)
            return url
        except Exception as e:
            logger.warning("AUTH: Failed to parse publishable key: %s", e)

    raise RuntimeError(
        "Cannot determine Clerk JWKS URL. "
        "Set at least one of: CLERK_JWKS_URL, CLERK_JWT_ISSUER, or NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
    )


def _get_jwks_client() -> PyJWKClient:
    """Lazily initializes and returns the JWKS client."""
    global _jwks_client
    if _jwks_client is None:
        jwks_url = _resolve_jwks_url()
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
        logger.info("AUTH: Initialized JWKS client → %s", jwks_url)
    return _jwks_client


def _decode_jwt_header_unsafe(token: str) -> dict:
    """Decodes the JWT header WITHOUT verification — purely for diagnostics."""
    try:
        header_b64 = token.split(".")[0]
        padded = header_b64 + "=" * (-len(header_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(padded))
    except Exception:
        return {}


def _decode_jwt_payload_unsafe(token: str) -> dict:
    """Decodes the JWT payload WITHOUT verification — purely for diagnostics."""
    try:
        payload_b64 = token.split(".")[1]
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        return json.loads(base64.urlsafe_b64decode(padded))
    except Exception:
        return {}


# ──────────────────────────────────────────────────────────
# FastAPI dependency
# ──────────────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    FastAPI dependency that verifies a Clerk JWT token via JWKS.

    Returns the Clerk user_id (the 'sub' claim) on success.
    Raises HTTPException(401) on any verification failure.
    """
    token = credentials.credentials

    # ── Diagnostic header dump (non-fatal; errors here must not crash auth) ──
    try:
        header = _decode_jwt_header_unsafe(token)
        unverified = _decode_jwt_payload_unsafe(token)
        logger.debug(
            "AUTH AUDIT: token_prefix=%s... len=%d alg=%s kid=%s iss=%s sub=%s",
            token[:15] if token else "EMPTY",
            len(token) if token else 0,
            header.get("alg", "?"),
            header.get("kid", "?"),
            unverified.get("iss", "?"),
            unverified.get("sub", "?"),
        )
    except Exception as e:
        logger.warning("AUTH: Failed to decode JWT header for diagnostics: %s", e)
        # Diagnostic block — never raise here, let real verification below handle it
        header = {}
        unverified = {}

    try:
        jwks_client = _get_jwks_client()

        # Fetch the public key that matches this token's 'kid'
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        logger.debug("AUTH: Got signing key kid=%s", signing_key.key_id)

        # Determine expected issuer (if set)
        expected_issuer = settings.CLERK_JWT_ISSUER or None

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=expected_issuer,
            options={
                "verify_exp": True,
                "verify_iss": bool(expected_issuer),
                "verify_aud": False,  # Clerk doesn't always set audience
            },
            leeway=60  # Forgive up to 60 seconds of clock skew
        )

        user_id = payload.get("sub")
        if not user_id:
            logger.warning("AUTH: Token verified but missing 'sub' claim. Payload keys: %s", list(payload.keys()))
            raise HTTPException(status_code=401, detail="Token missing 'sub' claim")

        logger.debug("AUTH: ✓ Verified user_id=%s", user_id)
        return user_id

    except jwt.ExpiredSignatureError:
        logger.warning("AUTH REJECT: Token EXPIRED for sub=%s", unverified.get("sub", "?"))
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidIssuerError:
        token_iss = unverified.get("iss", "unknown")
        logger.warning(
            "AUTH REJECT: Issuer mismatch. Token has iss='%s', backend expects='%s'. "
            "Fix CLERK_JWT_ISSUER in your backend .env!",
            token_iss,
            settings.CLERK_JWT_ISSUER,
        )
        raise HTTPException(
            status_code=401,
            detail=f"Issuer mismatch: token='{token_iss}' vs expected='{settings.CLERK_JWT_ISSUER}'",
        )

    except jwt.exceptions.PyJWKClientError as e:
        logger.error("AUTH REJECT: JWKS fetch/match failed: %s", e)
        raise HTTPException(status_code=401, detail="Unable to fetch signing keys from Clerk")

    except jwt.DecodeError as e:
        logger.warning("AUTH REJECT: Decode error (malformed JWT): %s", e)
        raise HTTPException(status_code=401, detail="Invalid token format")

    except jwt.InvalidTokenError as e:
        logger.warning("AUTH REJECT: Generic verification failure: %s (type=%s)", e, type(e).__name__)
        raise HTTPException(status_code=401, detail="Invalid token")

    except RuntimeError as e:
        logger.error("AUTH CONFIG ERROR: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error("AUTH UNEXPECTED: %s (type=%s)", e, type(e).__name__, exc_info=True)
        raise HTTPException(status_code=401, detail="Authentication failed")

async def verify_workspace_access(
    workspace_id: str | None = Header(default=None, alias="x-workspace-id"),
    user_id: str = Depends(get_current_user)
) -> str | None:
    """
    Verifies that the current user has access to the specified workspace.
    Returns the workspace_id on success, or None if backward-compatibility fallback is used.
    Raises 403 Forbidden if access is explicitly denied.
    """
    if not workspace_id:
        # Fallback for two-phase rollout: allow requests without workspace_id
        # We only log for now because compare.py still relies on this behavior.
        logger.warning("AUTH AUDIT: Deprecated fallback used — missing x-workspace-id header for user=%s", user_id)
        return None
        
    try:
        supabase = get_supabase()
        response = supabase.table("workspace_members").select("id").eq("workspace_id", workspace_id).eq("user_id", user_id).limit(1).execute()
        if not response.data:
            logger.warning("AUTH REJECT: user_id=%s attempted to access workspace_id=%s without permission", user_id, workspace_id)
            raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this workspace")
        return workspace_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Workspace verification error: %s", e)
        raise HTTPException(status_code=500, detail="Error verifying workspace access")

async def verify_workspace_path(
    workspace_id: str,
    user_id: str = Depends(get_current_user)
) -> str:
    """
    Verifies that the current user has access to the workspace_id provided in the URL path.
    Raises 403 Forbidden if access is explicitly denied.
    """
    if not workspace_id:
        raise HTTPException(status_code=400, detail="workspace_id is required")
        
    try:
        supabase = get_supabase()
        response = supabase.table("workspace_members").select("id").eq("workspace_id", workspace_id).eq("user_id", user_id).limit(1).execute()
        if not response.data:
            logger.warning("AUTH REJECT: user_id=%s attempted to access workspace_id=%s without permission", user_id, workspace_id)
            raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this workspace")
        return workspace_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Workspace path verification error: %s", e)
        raise HTTPException(status_code=500, detail="Error verifying workspace access")

