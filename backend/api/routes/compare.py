import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks
from api.schemas.compare import (
    CompareRequest, CompareResponse, GetComparisonResponse,
    SaveCompareRequest, SaveCompareResponse, SuggestionsResponse,
    SavedComparisonsResponse
)
from services import suggestion_service, compare_service
from agents.graph.comparison_graph import comparison_graph

router = APIRouter()

def _run_comparison_memory_task(final_state: dict):
    try:
        print("[DEBUG: compare_route] Starting background memory creation for comparison.")
        from agents.nodes.create_memory import create_memory
        from agents.nodes.store_memory import store_memory
        print("[DEBUG: compare_route] Calling create_memory...")
        memory_state = create_memory(final_state)
        print("[DEBUG: compare_route] Calling store_memory...")
        store_memory(memory_state)
        print("[DEBUG: compare_route] Background memory creation completed.")
    except Exception as e:
        print(f"[DEBUG: compare_route] Comparison memory creation failed: {e}")

@router.post("", response_model=CompareResponse)
def submit_comparison(body: CompareRequest, background_tasks: BackgroundTasks):
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
        visuals=visuals
    )
    
    # Background memory creation
    final_state["comparison_id"] = comparison_id
    background_tasks.add_task(_run_comparison_memory_task, final_state)
    
    return CompareResponse(
        comparison_id=comparison_id,
        comparison=created
    )

@router.get("/saved", response_model=SavedComparisonsResponse)
def get_saved_comparisons():
    comps = compare_service.get_saved_comparisons()
    return SavedComparisonsResponse(comparisons=comps)

from services.cache_service import cache

@router.get("/{comparison_id}", response_model=GetComparisonResponse)
def get_comparison(comparison_id: str):
    cache_key = f"comp_{comparison_id}"
    cached_comp = cache.get(cache_key)
    if cached_comp:
        return GetComparisonResponse(comparison=cached_comp)

    comp = compare_service.get_comparison(comparison_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comparison not found.")
        
    cache.set(cache_key, comp)
    return GetComparisonResponse(comparison=comp)

@router.post("/save", response_model=SaveCompareResponse)
def save_comparison(body: SaveCompareRequest):
    success = compare_service.save_comparison(body.comparison_id)
    return SaveCompareResponse(saved=success)

@router.get("/suggestions/{session_id}", response_model=SuggestionsResponse)
def get_suggestions(session_id: str):
    suggs = suggestion_service.get_suggestions(session_id)
    return SuggestionsResponse(suggestions=suggs)
