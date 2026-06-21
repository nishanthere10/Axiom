import httpx
import logging
from core.config import settings

logger = logging.getLogger(__name__)

async def get_github_oauth_token(user_id: str) -> str | None:
    """
    Fetch the GitHub OAuth access token for a given user from Clerk Backend API.
    """
    if not settings.CLERK_SECRET_KEY:
        logger.error("CLERK_SECRET_KEY is not configured.")
        return None

    url = f"https://api.clerk.com/v1/users/{user_id}/oauth_access_tokens/oauth_github"
    headers = {
        "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data and isinstance(data, list) and len(data) > 0:
                return data[0].get("token")
            return None
    except Exception as e:
        logger.error(f"Failed to fetch GitHub OAuth token from Clerk for user {user_id}: {e}")
        return None
