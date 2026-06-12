from fastapi import APIRouter, Depends
from services.health_service import run_all_checks
from core.auth import get_current_user

router = APIRouter()

@router.get("/health")
async def get_admin_health(user_id: str = Depends(get_current_user)):
    """
    GET /admin/health
    Returns detailed health status for all dependencies.
    Requires authentication.
    """
    return await run_all_checks()
