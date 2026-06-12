import jwt
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

def get_clerk_user_id(request: Request) -> str:
    """
    Extracts the Clerk user_id from the Authorization header for rate limiting.
    Does not perform full cryptographic verification (which is handled by core.auth.py).
    Falls back to IP address if token is missing/invalid.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return get_remote_address(request)
    
    token = auth_header.split(" ")[1]
    try:
        # Decode without verification just to extract 'sub' for the rate limit key.
        # The actual route will reject invalid tokens securely.
        unverified_claims = jwt.decode(token, options={"verify_signature": False})
        user_id = unverified_claims.get("sub")
        if user_id:
            return user_id
    except Exception:
        pass
        
    return get_remote_address(request)

# Initialize the limiter with our custom key function
limiter = Limiter(key_func=get_clerk_user_id)
