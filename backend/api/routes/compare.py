import logging
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from api.schemas.compare import (
    CompareRequest, CompareResponse, GetComparisonResponse,
    SaveCompareRequest, SaveCompareResponse, SuggestionsResponse,
    SavedComparisonsResponse
)
from services.cache_service import cache
from services import compare_service
from agents.graph.comparison_graph import comparison_graph
from core.auth import get_current_user
from middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("", response_model=CompareResponse)
@limiter.limit("3/minute")
def submit_comparison(request: Request, body: CompareRequest, background_tasks: BackgroundTasks, user_id: str = Depends(get_current_user)):
    if body.session_a == body.session_b:
        raise HTTPException(status_code=400, detail="Cannot compare a session with itself.")
        
    comparison_id = str(uuid.uuid4())
    
    # Synchronous execution of the graph
    initial_state = {
        "session_a_id": body.session_a,
        "session_b_id": body.session_b,
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
    )
    
    # Queue persistent memory job
    try:
        from services import memory_job_service
        payload = {
            "session_a_id": body.session_a,
            "session_b_id": body.session_b,
            "comparison_id": comparison_id,
            "structural_diff": diff,
            "decision_evolution": evo,
            "impact_summary": imp
        }
        memory_job_service.create_job(
            user_id=user_id,
            session_id=comparison_id,
            payload=payload
        )
    except Exception as memory_exc:
        logger.warning("Failed to queue comparison memory job: %s", memory_exc)

    try:
        from services.metrics_service import increment_comparison_count
        increment_comparison_count()
    except Exception as e:
        logger.warning(f"Failed to increment comparison metric: {e}")
    
    return CompareResponse(
        comparison_id=comparison_id,
        comparison=created
    )

@router.get("/saved", response_model=SavedComparisonsResponse)
def get_saved_comparisons(user_id: str = Depends(get_current_user)):
    comps = compare_service.get_saved_comparisons(user_id=user_id)
    return SavedComparisonsResponse(comparisons=comps)

@router.get("/{comparison_id}", response_model=GetComparisonResponse)
def get_comparison(comparison_id: str, user_id: str = Depends(get_current_user)):
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
