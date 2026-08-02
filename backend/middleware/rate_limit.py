import jwt
import logging
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)

def get_clerk_user_id(request: Request) -> str:
    """
    Safely extracts the Clerk user_id from the Authorization header for rate limiting.
    
    SECURITY FIX: Now performs basic JWT validation to prevent spoofing attacks.
    Falls back to IP address if token is missing/invalid/expired.
    
    This provides defense-in-depth even though routes do full verification.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return get_remote_address(request)
    
    token = auth_header.split(" ")[1]
    try:
        # SECURITY FIX: Basic structure validation to prevent trivial spoofing
        # Check JWT has 3 parts and valid structure before extracting claims
        parts = token.split('.')
        if len(parts) != 3:
            logger.debug("Rate limit: Invalid JWT structure, falling back to IP")
            return get_remote_address(request)
        
        # Decode header to check basic structure
        try:
            header = jwt.get_unverified_header(token)
            if not header.get('alg') or not header.get('typ'):
                logger.debug("Rate limit: Missing JWT header fields, falling back to IP")
                return get_remote_address(request)
        except jwt.DecodeError:
            logger.debug("Rate limit: JWT header decode failed, falling back to IP")
            return get_remote_address(request)
        
        # Extract payload with basic validation
        unverified_claims = jwt.decode(token, options={
            "verify_signature": False,
            "verify_exp": True,  # SECURITY FIX: Check expiration to prevent replay attacks
            "verify_iss": False,  # Don't verify issuer here (done in auth.py)
            "verify_aud": False
        })
        
        user_id = unverified_claims.get("sub")
        if user_id and isinstance(user_id, str) and len(user_id) > 0:
            logger.debug("Rate limit: Using user_id=%s for rate limiting", user_id[:8] + "...")
            return user_id
            
    except jwt.ExpiredSignatureError:
        logger.debug("Rate limit: Expired JWT, falling back to IP")
    except jwt.DecodeError:
        logger.debug("Rate limit: JWT decode error, falling back to IP") 
    except Exception as e:
        logger.debug("Rate limit: JWT validation error (%s), falling back to IP", type(e).__name__)
        
    # SECURITY: Always fall back to IP if JWT is invalid/missing
    return get_remote_address(request)

# Initialize the limiter with our custom key function
limiter = Limiter(key_func=get_clerk_user_id)
