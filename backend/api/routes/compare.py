import logging
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request, Header
from api.schemas.compare import (
    CompareRequest, CompareResponse, GetComparisonResponse,
    SaveCompareRequest, SaveCompareResponse, SuggestionsResponse,
    SavedComparisonsResponse
)
from services.cache_service import cache
from services import compare_service
from agents.graph.comparison_graph import comparison_graph
from core.auth import get_current_user, verify_workspace_access
from middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=CompareResponse)
@limiter.limit("5/minute")
def submit_comparison(request: Request, body: CompareRequest, background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user), workspace_id: str | None = Depends(verify_workspace_access)):
    if body.session_a == body.session_b:
        raise HTTPException(status_code=400, detail="Cannot compare a session with itself.")
        
    import time
    start_time = time.time()
    
    comparison_id = str(uuid.uuid4())
    
    # Synchronous execution of the graph
    initial_state = {
        "session_a_id": body.session_a,
        "session_b_id": body.session_b,
        "user_id": user_id,
        "status": "starting"
    }
    
    try:
        final_state = comparison_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
        
    # Extract results
    diff = final_state.get("structural_diff", {})
    evo = final_state.get("decision_evolution", "")
    imp = final_state.get("impact_summary", "")
    visuals = final_state.get("visuals", [])
    memory_context = final_state.get("memory_context", {})
    summary = f"Comparison of {body.session_a} and {body.session_b}"
    
    # Embed memory_context into impact_summary to avoid needing a Supabase migration for comparisons
    if memory_context and imp:
        if isinstance(imp, dict):
            imp["memory_context"] = memory_context
            
    # Save the row to the database (saved=false initially)
    created = compare_service.create_comparison(
        comparison_id=comparison_id,
        session_a=body.session_a,
        session_b=body.session_b,
        summary=summary,
        structural_diff=diff,
        decision_evolution=evo,
        impact_summary=imp,
        visuals=visuals,
        user_id=user_id,
        workspace_id=workspace_id,
    )
    
    # Queue persistent memory job
    # Memory generation for comparisons is now deferred until explicitly approved.
    logger.debug("Comparison completed. Decision record memory deferral applied.")

    try:
        import time
        from services.metrics_service import emit_comparison_completed
        latency_ms = int((time.time() - start_time) * 1000)
        emit_comparison_completed(user_id=user_id, latency_ms=latency_ms, confidence=0.0)
    except Exception as e:
        logger.warning(f"Failed to emit comparison metric: {e}")
    
    return CompareResponse(
        comparison_id=comparison_id,
        comparison=created
    )

@router.get("/saved", response_model=SavedComparisonsResponse)
def get_saved_comparisons(user_id: str = Depends(get_current_user), workspace_id: str | None = Depends(verify_workspace_access)):
    comps = compare_service.get_saved_comparisons(user_id=user_id, workspace_id=workspace_id)
    return SavedComparisonsResponse(comparisons=comps)

@router.get("/history", response_model=SavedComparisonsResponse)
def get_comparison_history(limit: int = 10, offset: int = 0, user_id: str = Depends(get_current_user), workspace_id: str | None = Depends(verify_workspace_access)):
    comparisons = compare_service.get_recent_comparisons(limit=limit, offset=offset, user_id=user_id, workspace_id=workspace_id)
    return SavedComparisonsResponse(comparisons=comparisons)

@router.get("/{comparison_id}", response_model=GetComparisonResponse)
def get_comparison(comparison_id: str, user_id: str = Depends(get_current_user), workspace_id: str | None = Depends(verify_workspace_access)):
    cache_key = f"comp_{user_id}_{comparison_id}"
    cached_comp = cache.get(cache_key)
    if cached_comp:
        return GetComparisonResponse(comparison=cached_comp)

    comp = compare_service.get_comparison(comparison_id, user_id=user_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comparison not found.")
        
    cache.set(cache_key, comp)
    return GetComparisonResponse(comparison=comp)

@router.post("/save", response_model=SaveCompareResponse)
def save_comparison(body: SaveCompareRequest, user_id: str = Depends(get_current_user)):
    success = compare_service.save_comparison(body.comparison_id, user_id=user_id)
    return SaveCompareResponse(saved=success)
