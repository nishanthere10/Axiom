"""
SECURITY FIX: Circuit breaker monitoring endpoints for operational visibility.

Provides health monitoring and circuit breaker reset capabilities for administrators.
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from core.auth import get_current_user, verify_workspace_owner_access
from services.circuit_breaker import circuit_manager

logger = logging.getLogger(__name__)
router = APIRouter()

class CircuitBreakerResetRequest(BaseModel):
    breaker_name: str
    reason: Optional[str] = None

@router.get("/status")
def get_circuit_breaker_status(
    user_id: str = Depends(get_current_user),
    workspace_id: str = Depends(verify_workspace_owner_access),
):
    """
    GET /circuit-breakers/status
    Returns status of all circuit breakers. Requires workspace owner access.
    """
    try:
        stats = circuit_manager.get_all_stats()
        
        # Calculate overall health
        total_breakers = len(stats)
        open_breakers = sum(1 for s in stats.values() if s["state"] == "open")
        half_open_breakers = sum(1 for s in stats.values() if s["state"] == "half_open")
        
        overall_health = "healthy"
        if open_breakers > 0:
            overall_health = "degraded" if open_breakers < total_breakers else "critical"
        elif half_open_breakers > 0:
            overall_health = "recovering"
        
        return {
            "overall_health": overall_health,
            "summary": {
                "total_breakers": total_breakers,
                "open_breakers": open_breakers,
                "half_open_breakers": half_open_breakers,
                "closed_breakers": total_breakers - open_breakers - half_open_breakers,
            },
            "circuit_breakers": stats,
            "recommendations": _get_health_recommendations(stats)
        }
        
    except Exception as e:
        logger.error(f"Failed to get circuit breaker status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get circuit breaker status")

@router.post("/reset")
def reset_circuit_breaker(
    body: CircuitBreakerResetRequest,
    user_id: str = Depends(get_current_user),
    workspace_id: str = Depends(verify_workspace_owner_access),
):
    """
    POST /circuit-breakers/reset
    Reset a specific circuit breaker to CLOSED state. Requires workspace owner access.
    """
    try:
        success = circuit_manager.reset_breaker(body.breaker_name)
        
        if not success:
            raise HTTPException(
                status_code=404, 
                detail=f"Circuit breaker '{body.breaker_name}' not found"
            )
        
        # Log the reset action
        logger.info(
            f"Circuit breaker '{body.breaker_name}' reset by user {user_id}. "
            f"Reason: {body.reason or 'No reason provided'}"
        )
        
        return {
            "success": True,
            "message": f"Circuit breaker '{body.breaker_name}' has been reset",
            "breaker_name": body.breaker_name,
            "reset_by": user_id,
            "reason": body.reason
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset circuit breaker {body.breaker_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset circuit breaker")

def _get_health_recommendations(stats: Dict[str, Dict[str, Any]]) -> list[str]:
    """Generate health recommendations based on circuit breaker states."""
    recommendations = []
    
    for name, breaker_stats in stats.items():
        state = breaker_stats["state"]
        failure_rate = breaker_stats.get("failure_rate", 0)
        
        if state == "open":
            recommendations.append(
                f"Circuit breaker '{name}' is OPEN - investigate underlying service health"
            )
        elif state == "half_open":
            recommendations.append(
                f"Circuit breaker '{name}' is testing recovery - monitor for stability"
            )
        elif failure_rate > 0.3:  # 30% failure rate threshold
            recommendations.append(
                f"Circuit breaker '{name}' has high failure rate ({failure_rate:.1%}) - investigate intermittent issues"
            )
    
    if not recommendations:
        recommendations.append("All circuit breakers are healthy")
    
    return recommendations