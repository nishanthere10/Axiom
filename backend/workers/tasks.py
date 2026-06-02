from agents.graph.decision_graph import decision_graph
from services import research_service

# Progress milestones per node (used when streaming the graph)
_NODE_PROGRESS = {
    "decompose_question": (2, 5),
    "retrieve_memory": (5, 10),
    "analyze_memory": (10, 15),
    "canonicalize_topic": (15, 20),
    "generate_queries": (20, 25),
    "collect_and_score_evidence": (25, 45),
    "generate_decision": (45, 70),
    "build_confidence": (70, 80),
    "generate_visual_spec": (80, 88),
    "validate_visual_spec": (88, 92),
    "format_document": (92, 100),
}


def run_research_background_task(session_id: str, job_id: str, question: str, force_refresh: bool = False) -> dict:
    """
    Background task that runs the LangGraph decision pipeline natively via FastAPI.

    Steps:
    1. Mark job as running.
    2. Stream the graph, updating progress after each node.
    3. On success: save document, mark session + job complete.
    4. On failure: mark job failed and re-raise (triggers retry if eligible).
    """
    try:
        # 1. Mark job as running
        research_service.update_job_status(job_id, status="running", progress=5, step="starting")

        # 2. Stream the graph — get state updates after each node
        current_state = {
            "question": question, 
            "summary": "", 
            "recommendation": "", 
            "tradeoffs": "", 
            "alternatives": "", 
            "confidence": {},
            "canonical_slug": "",
            "queries": [],
            "evidence": [],
            "consensus": "",
            "force_refresh": force_refresh,
            "visual_specs": [],
            "visuals": [],
            "retrieved_memories": [],
            "memory_context": {},
            "status": "starting"
        }
        
        for chunk in decision_graph.stream(current_state):
            for node_name, node_state in chunk.items():
                # LangGraph stream yields only the updates from the current node.
                # We must accumulate them to have the full state for saving.
                current_state.update(node_state)
                
                _, progress = _NODE_PROGRESS.get(node_name, (0, 0))
                research_service.update_job_status(
                    job_id,
                    status="running",
                    progress=progress,
                    step=node_name,
                )
                
        final_state = current_state

        if final_state is None or final_state.get("status") != "complete":
            raise ValueError("Graph did not complete successfully.")

        # 3. Save the decision document
        research_service.save_document(
            session_id=session_id,
            question=question,
            state=final_state,
        )

        # 4. Mark session and job as complete
        research_service.update_session_status(session_id, "complete")
        research_service.update_job_status(job_id, status="completed", progress=100, step="done")

        # 5. Background Memory Creation
        # This executes safely in the background worker thread *after* the user sees 100% complete
        try:
            print("[DEBUG: tasks] Starting background memory creation for research session.")
            from agents.nodes.create_memory import create_memory
            from agents.nodes.store_memory import store_memory
            
            final_state["session_id"] = session_id
            print("[DEBUG: tasks] Calling create_memory...")
            memory_state = create_memory(final_state)
            print("[DEBUG: tasks] Calling store_memory...")
            store_memory(memory_state)
            print("[DEBUG: tasks] Background memory creation completed.")
        except Exception as memory_exc:
            print(f"[DEBUG: tasks] Memory creation failed (non-fatal): {memory_exc}")

        return {"session_id": session_id, "job_id": job_id, "status": "completed"}

    except Exception as exc:
        research_service.update_job_status(job_id, status="failed", progress=0, step="error")
        research_service.update_session_status(session_id, "failed")
        raise
