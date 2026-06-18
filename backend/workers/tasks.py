import logging
from agents.graph.decision_graph import decision_graph
from services import research_service

logger = logging.getLogger(__name__)

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


def run_research_background_task(session_id: str, job_id: str, question: str, force_refresh: bool = False, user_id: str = "anonymous") -> dict:
    """
    Background task that runs the LangGraph decision pipeline natively via FastAPI.

    Steps:
    1. Mark job as running.
    2. Stream the graph, updating progress after each node.
    3. On success: save document, mark session + job complete.
    4. On failure: mark job failed and re-raise (triggers retry if eligible).
    """
    try:
        import time
        start_time = time.time()
        
        # 1. Mark job as running
        research_service.update_job_status(job_id, status="running", progress=5, step="starting")

        # 2. Stream the graph — get state updates after each node
        current_state = {
            "question": question, 
            "user_id": user_id,  # ADDED: Required for retrieve_memory to search the correct Pinecone namespace
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
            "github_context": [],
            "warnings": [],
            "status": "starting"
        }
        
        max_progress = 5
        for chunk in decision_graph.stream(current_state):
            for node_name, node_state in chunk.items():
                # LangGraph stream yields only the updates from the current node.
                # We must accumulate them to have the full state for saving.
                current_state.update(node_state)
                
                _, progress = _NODE_PROGRESS.get(node_name, (0, 0))
                if progress > max_progress:
                    max_progress = progress
                    
                research_service.update_job_status(
                    job_id,
                    status="running",
                    progress=max_progress,
                    step=node_name,
                )
                
        final_state = current_state

        if final_state is None or final_state.get("status") != "complete":
            raise ValueError("Graph did not complete successfully.")

        # 3. Save the decision document
        pipeline_warnings = final_state.get("warnings", [])
        research_service.save_document(
            session_id=session_id,
            question=question,
            state=final_state,
            user_id=user_id,
            warnings=pipeline_warnings,
        )

        # 4. Mark session and job as complete
        logger.info(f"Research job {job_id} completed successfully.")
        research_service.update_job_status(job_id, status="completed", progress=100, step="done")
        research_service.update_session_status(session_id, "complete")

        # Record metrics
        try:
            import time
            import threading
            from services.metrics_service import emit_research_completed
            from services.topic_classifier import classify_topic_background
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            evidence_list = final_state.get("evidence", [])
            evidence_count = len(evidence_list)
            sources_used = len(set([e.get("url", "") for e in evidence_list if e.get("url")]))
            
            conf_dict = final_state.get("confidence", {})
            conf_score = 0.0
            if conf_dict and isinstance(conf_dict, dict):
                scores = [v for v in conf_dict.values() if isinstance(v, (int, float))]
                if scores:
                    conf_score = sum(scores) / len(scores)
                    
            emit_research_completed(
                user_id=user_id,
                latency_ms=latency_ms,
                confidence=conf_score,
                evidence_count=evidence_count,
                sources_used=sources_used
            )
            
            # Fire and forget topic classification
            threading.Thread(target=classify_topic_background, args=(question, user_id), daemon=True).start()
        except Exception as e:
            logger.warning(f"Failed to emit research metric: {e}")

        # 5. Background Memory Creation
        # We now use a durable Postgres-backed job queue instead of fire-and-forget
        try:
            logger.debug("Queueing persistent memory job for research session.")
            from services import memory_job_service
            
            # Extract just the necessary state payload (we don't need everything)
            payload = {
                "question": final_state.get("question"),
                "recommendation": final_state.get("recommendation_context", final_state.get("recommendation", "")),
                "evidence": final_state.get("evidence", [])
            }
            memory_job_service.create_job(
                user_id=user_id,
                session_id=session_id,
                payload=payload
            )
            logger.debug("Memory job queued successfully.")
        except Exception as memory_exc:
            logger.warning("Failed to queue memory job: %s", memory_exc)

        return {"session_id": session_id, "job_id": job_id, "status": "completed"}

    except Exception as exc:
        logger.error("Research background task failed: %s", exc, exc_info=True)
        research_service.update_job_status(job_id, status="failed", progress=0, step="error")
        research_service.update_session_status(session_id, "failed")
        raise
