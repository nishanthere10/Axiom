import logging
import httpx
import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cachetools import TTLCache
from core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Cache JWKS keys for 1 hour — they rotate infrequently
_jwks_cache = TTLCache(maxsize=4, ttl=3600)
_jwks_client = None


def _get_jwks_client() -> PyJWKClient:
    """Lazily initializes the JWKS client for Clerk's public keys."""
    global _jwks_client
    if _jwks_client is None:
        issuer = settings.CLERK_JWT_ISSUER
        if not issuer:
            raise RuntimeError("CLERK_JWT_ISSUER is not configured")
        jwks_url = f"{issuer}/.well-known/jwks.json"
        _jwks_client = PyJWKClient(jwks_url, cache_keys=True)
        logger.debug("Initialized JWKS client with URL: %s", jwks_url)
    return _jwks_client


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    FastAPI dependency that verifies a Clerk JWT token.
    
    Returns the Clerk user_id (the 'sub' claim) on success.
    Raises HTTPException(401) on any verification failure.
    """
    token = credentials.credentials

    try:
        jwks_client = _get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=settings.CLERK_JWT_ISSUER,
            options={
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": False,  # Clerk doesn't always set audience
            },
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Token missing 'sub' claim")

        return user_id

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidIssuerError:
        logger.warning("JWT invalid issuer")
        raise HTTPException(status_code=401, detail="Invalid token issuer")
    except jwt.InvalidTokenError as e:
        logger.warning("JWT verification failed: %s", e)
        raise HTTPException(status_code=401, detail="Invalid token")
    except RuntimeError as e:
        logger.error("Auth configuration error: %s", e)
        raise HTTPException(status_code=500, detail="Authentication not configured")
    except Exception as e:
        logger.error("Unexpected auth error: %s", e, exc_info=True)
        raise HTTPException(status_code=401, detail="Authentication failed")
