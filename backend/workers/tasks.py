import logging
from agents.graph.decision_graph import decision_graph
from agents.callbacks.pipeline_logger import PipelineLogger
from services import research_service
from services.event_bus import publish as bus_publish

logger = logging.getLogger(__name__)

# Human-readable labels shown in the frontend progress UI
STEP_LABELS = {
    "decompose_question":          "Understanding your question…",
    "retrieve_memory":             "Checking your knowledge archive…",
    "retrieve_github_context":     "Reading your codebase…",
    "canonicalize_topic":          "Classifying topic…",
    "memory_relevance_evaluator":  "Evaluating memory relevance…",
    "analyze_memory":              "Analyzing past decisions…",
    "context_relevance_scorer":    "Filtering relevant context…",
    "generate_queries":            "Building research queries…",
    "collect_and_score_evidence":  "Searching and scoring evidence…",
    "generate_decision":           "Generating recommendation…",
    "build_confidence":            "Scoring confidence…",
    "generate_visual_spec":        "Creating diagrams…",
    "validate_visual_spec":        "Validating visuals…",
    "format_document":             "Assembling final report…",
}

# Deterministic progress value per node (never decreases)
NODE_PROGRESS = {
    "decompose_question":          5,
    "retrieve_memory":             10,
    "retrieve_github_context":     15,
    "canonicalize_topic":          18,
    "memory_relevance_evaluator":  22,
    "analyze_memory":              28,
    "context_relevance_scorer":    34,
    "generate_queries":            35,
    "collect_and_score_evidence":  58,
    "generate_decision":           72,
    "build_confidence":            80,
    "generate_visual_spec":        86,
    "validate_visual_spec":        92,
    "format_document":             97,
}




import anyio

async def run_research_background_task(session_id: str, job_id: str, question: str, user_id: str, force_refresh: bool = False, workspace_id: str | None = None) -> dict:
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
        await anyio.to_thread.run_sync(research_service.update_job_status, job_id, "running", 5, "starting")

        # 2. Stream the graph — get state updates after each node
        current_state = {
            "question": question, 
            "user_id": user_id,
            "workspace_id": workspace_id,
            "summary": "",
            "constraints": [],
            "reasoning": "",
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
        pipeline_cb = PipelineLogger(job_id=job_id, session_id=session_id)
        with anyio.move_on_after(900) as scope:
            async for chunk in decision_graph.astream(
                current_state,
                config={"callbacks": [pipeline_cb]},
            ):
                for node_name, node_state in chunk.items():
                    # LangGraph stream yields only the updates from the current node.
                    # We must accumulate them to have the full state for saving.
                    current_state.update(node_state)

                    progress = NODE_PROGRESS.get(node_name, max_progress)
                    if progress > max_progress:
                        max_progress = progress

                    step_label = STEP_LABELS.get(node_name, node_name)

                    # Build SSE metadata for retrieval nodes
                    meta: dict = {}
                    if node_name == "retrieve_memory":
                        memories = node_state.get("retrieved_memories", [])
                        meta["memories_found"] = len(memories)
                        if memories:
                            meta["memory_summaries"] = [
                                m.get("metadata", {}).get("summary", "")[:80]
                                for m in memories[:3]
                            ]
                    elif node_name == "retrieve_github_context":
                        chunks = node_state.get("github_context", [])
                        meta["github_chunks"] = len(chunks)

                    # Publish to SSE event bus (non-blocking)
                    await bus_publish(job_id, {
                        "status":   "running",
                        "progress": max_progress,
                        "step":     step_label,
                        "node":     node_name,
                        "meta":     meta,
                    })

                    # Also update Supabase for polling fallback
                    await anyio.to_thread.run_sync(
                        research_service.update_job_status,
                        job_id,
                        "running",
                        max_progress,
                        step_label,
                    )

        if scope.cancel_called:
            logger.error("Research job %s timed out", job_id)
            await anyio.to_thread.run_sync(research_service.update_job_status, job_id, "failed", 0, "timeout")
            await anyio.to_thread.run_sync(research_service.update_session_status, session_id, "failed")
            return {"session_id": session_id, "job_id": job_id, "status": "timeout"}
                
        final_state = current_state

        if final_state is None or final_state.get("status") != "complete":
            actual_status = final_state.get("status") if final_state else None
            logger.error(
                "Research job %s: graph finished but status='%s' (expected 'complete'). "
                "format_document node may not have run. Check graph fan-in edges.",
                job_id, actual_status
            )
            raise ValueError(f"Graph did not complete successfully. Final status='{actual_status}'")

        try:
            from services.db import get_supabase
            supabase = get_supabase()
            
            scored_mems = final_state.get("scored_memories", [])
            scored_git  = final_state.get("scored_github", [])
            retrieved_mems = final_state.get("retrieved_memories", [])
            retrieved_git  = final_state.get("github_context", [])

            mem_scores = [m.get("relevance_score", 0) for m in scored_mems]
            git_scores = [g.get("relevance_score", 0) for g in scored_git]

            await anyio.to_thread.run_sync(
                lambda: supabase.table("context_relevance_log").insert({
                    "session_id":         session_id,
                    "user_id":            user_id,
                    "workspace_id":       workspace_id,
                    "memories_retrieved": len(retrieved_mems),
                    "memories_injected":  len(scored_mems),
                    "github_retrieved":   len(retrieved_git),
                    "github_injected":    len(scored_git),
                    "total_dropped":      final_state.get("dropped_context_count", 0),
                    "best_memory_score":  max(mem_scores) if mem_scores else None,
                    "worst_memory_score": min(mem_scores) if mem_scores else None,
                    "best_github_score":  max(git_scores) if git_scores else None,
                    "worst_github_score": min(git_scores) if git_scores else None,
                }).execute()
            )
        except Exception as e:
            logger.warning("Failed to write context_relevance_log (non-fatal): %s", e)

        # 3. Save the decision document
        pipeline_warnings = final_state.get("warnings", [])
        await anyio.to_thread.run_sync(
            research_service.save_document,
            session_id,
            question,
            final_state,
            user_id,
            pipeline_warnings
        )

        # 4. Mark session and job as complete
        logger.info(f"Research job {job_id} completed successfully.")
        await anyio.to_thread.run_sync(research_service.update_job_status, job_id, "completed", 100, "Done")
        await anyio.to_thread.run_sync(research_service.update_session_status, session_id, "complete")

        # Publish terminal SSE event so the frontend closes the EventSource
        await bus_publish(job_id, {
            "status":     "completed",
            "progress":   100,
            "step":       "Done",
            "session_id": session_id,
        })

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
                    
            await anyio.to_thread.run_sync(
                emit_research_completed,
                user_id,
                latency_ms,
                conf_score,
                evidence_count,
                sources_used
            )
            
            # Fire and forget topic classification
            threading.Thread(target=classify_topic_background, args=(question, user_id), daemon=True).start()
        except Exception as e:
            logger.warning(f"Failed to emit research metric: {e}")

        # 5. Background Memory Creation
        # Enqueue a memory job so the sweeper writes this decision to Supabase + Pinecone.
        # This is fire-and-forget — failures here do not fail the research job.
        try:
            from services.memory_job_service import create_job
            memory_payload = {
                "question": question,
                "recommendation": final_state.get("recommendation", ""),
                "summary": final_state.get("summary", ""),
                "tradeoffs": final_state.get("tradeoffs", ""),
                "alternatives": final_state.get("alternatives", ""),
                "workspace_id": workspace_id,  # Critical: stamps memory to the correct workspace
            }
            await anyio.to_thread.run_sync(create_job, user_id, session_id, memory_payload)
            logger.debug("Memory job enqueued for session %s", session_id)
        except Exception as e:
            logger.warning("Failed to enqueue memory job (non-fatal): %s", e)

        return {"session_id": session_id, "job_id": job_id, "status": "completed"}

    except Exception as exc:
        logger.error("Research background task failed: %s", exc, exc_info=True)
        await anyio.to_thread.run_sync(research_service.update_job_status, job_id, "failed", 0, "error")
        await anyio.to_thread.run_sync(research_service.update_session_status, session_id, "failed")
        # Publish failure event so the frontend can show an error state
        await bus_publish(job_id, {
            "status":   "failed",
            "progress": 0,
            "step":     "Research failed",
            "error":    str(exc)[:200],
        })
        raise
