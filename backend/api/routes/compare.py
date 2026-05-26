import uuid
from fastapi import APIRouter, HTTPException
from api.schemas.compare import (
    CompareRequest, CompareResponse, GetComparisonResponse,
    SaveCompareRequest, SaveCompareResponse, SuggestionsResponse,
    SavedComparisonsResponse
)
from services import suggestion_service, compare_service
from agents.graph.comparison_graph import comparison_graph

router = APIRouter()

@router.post("", response_model=CompareResponse)
def submit_comparison(body: CompareRequest):
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
    summary = f"Comparison of {body.session_a} and {body.session_b}"
    
    # Save the row to the database (saved=false initially)
    created = compare_service.create_comparison(
        comparison_id=comparison_id,
        session_a=body.session_a,
        session_b=body.session_b,
        summary=summary,
        structural_diff=diff,
        decision_evolution=evo,
        impact_summary=imp
    )
    
    return CompareResponse(
        comparison_id=comparison_id,
        comparison=created
    )

@router.get("/saved", response_model=SavedComparisonsResponse)
def get_saved_comparisons():
    comps = compare_service.get_saved_comparisons()
    return SavedComparisonsResponse(comparisons=comps)

@router.get("/{comparison_id}", response_model=GetComparisonResponse)
def get_comparison(comparison_id: str):
    comp = compare_service.get_comparison(comparison_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comparison not found.")
    return GetComparisonResponse(comparison=comp)

@router.post("/save", response_model=SaveCompareResponse)
def save_comparison(body: SaveCompareRequest):
    success = compare_service.save_comparison(body.comparison_id)
    return SaveCompareResponse(saved=success)

@router.get("/suggestions/{session_id}", response_model=SuggestionsResponse)
def get_suggestions(session_id: str):
    suggs = suggestion_service.get_suggestions(session_id)
    return SuggestionsResponse(suggestions=suggs)
