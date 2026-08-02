import logging
from agents.graph.decision_graph import decision_graph
from agents.callbacks.pipeline_logger import PipelineLogger
from services import research_service
from services.event_bus import publish as bus_publish
from services.circuit_breaker import circuit_manager, CircuitOpenError
import re
from typing import Dict, Any
import asyncio

logger = logging.getLogger(__name__)

# SECURITY FIX: Enhanced timeout configuration with circuit breakers
TIMEOUT_CONFIG = {
    "research_pipeline": {
        "total_timeout": 900,      # 15 minutes total
        "node_timeout": 120,       # 2 minutes per node
        "llm_timeout": 60,         # 1 minute per LLM call
        "search_timeout": 30,      # 30 seconds per search
        "memory_timeout": 15,      # 15 seconds per memory operation
    },
    "circuit_breaker": {
        "failure_threshold": 3,
        "failure_rate_threshold": 0.6,
        "recovery_timeout": 300,   # 5 minutes recovery
    }
}

async def _execute_with_timeout_and_circuit_breaker(
    operation_name: str, 
    operation_func, 
    timeout: int,
    *args, 
    **kwargs
) -> Any:
    """
    SECURITY FIX: Execute operation with circuit breaker and timeout protection.
    """
    breaker = circuit_manager.get_breaker(
        f"task_{operation_name}",
        failure_threshold=TIMEOUT_CONFIG["circuit_breaker"]["failure_threshold"],
        failure_rate_threshold=TIMEOUT_CONFIG["circuit_breaker"]["failure_rate_threshold"],
        recovery_timeout=TIMEOUT_CONFIG["circuit_breaker"]["recovery_timeout"],
        timeout=timeout
    )
    
    try:
        return await breaker.call(operation_func, *args, **kwargs)
    except CircuitOpenError:
        logger.error(f"Circuit breaker OPEN for {operation_name} - failing fast")
        raise TimeoutError(f"Service {operation_name} is currently unavailable (circuit breaker open)")
    except asyncio.TimeoutError:
        logger.error(f"Operation {operation_name} timed out after {timeout}s")
        raise TimeoutError(f"Operation {operation_name} timed out")

def _sanitize_error_message(error: Exception, context: str = "operation") -> str:
    """
    SECURITY FIX: Sanitize error messages to prevent information disclosure.
    
    Removes sensitive information like file paths, credentials, internal details
    while preserving useful information for debugging and user feedback.
    """
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # Define patterns that indicate sensitive information
    sensitive_patterns = [
        r'/[a-z_/]*\.py',  # File paths
        r'[a-zA-Z0-9_]*password[a-zA-Z0-9_]*',  # Password fields
        r'[a-zA-Z0-9_]*secret[a-zA-Z0-9_]*',    # Secret fields  
        r'[a-zA-Z0-9_]*key[a-zA-Z0-9_]*',       # Key fields
        r'token[a-zA-Z0-9_]*',                   # Token fields
        r'api[_-]?key',                          # API keys
        r'bearer [a-zA-Z0-9._-]+',               # Bearer tokens
        r'postgresql://[^\\s]+',                 # Database URLs
        r'mongodb://[^\\s]+',                    # MongoDB URLs
        r'redis://[^\\s]+',                      # Redis URLs
        r'http[s]?://[^\\s]*:[^\\s]*@',         # URLs with credentials
    ]
    
    # Check if error contains sensitive information
    contains_sensitive = any(re.search(pattern, error_str) for pattern in sensitive_patterns)
    
    if contains_sensitive:
        # Return generic message for sensitive errors
        return f"{context.title()} failed due to configuration issue"
    
    # Safe error types that can be exposed
    safe_errors = {
        'ConnectionError': f'{context.title()} connection failed',
        'TimeoutError': f'{context.title()} timed out',
        'HTTPException': f'{context.title()} request failed',
        'ValidationError': f'{context.title()} validation failed',
        'PermissionError': f'Permission denied for {context}',
        'FileNotFoundError': f'Required resource not found for {context}',
    }
    
    if error_type in safe_errors:
        return safe_errors[error_type]
    
    # For other errors, provide generic message
    return f'{context.title()} encountered an unexpected error'

def _create_safe_error_event(job_id: str, error: Exception, context: str = "research") -> Dict[str, Any]:
    """
    SECURITY FIX: Create sanitized error event for SSE streams.
    """
    return {
        "status": "failed",
        "progress": 0,
        "step": f"{context.title()} failed",
        "error": _sanitize_error_message(error, context),
        # Remove error_type to prevent fingerprinting
    }

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
    "assemble_context":            "Assembling engineering context…",
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
    "assemble_context":            65,
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

    SECURITY FIX: Enhanced with circuit breakers, timeouts, and graceful degradation.
    
    Steps:
    1. Mark job as running.
    2. Stream the graph with timeout protection, updating progress after each node.
    3. On success: save document, mark session + job complete.
    4. On failure: mark job failed and persist error details.
    """
    circuit_breaker_stats = {}
    
    try:
        import time
        start_time = time.time()
        
        # 1. Mark job as running with timeout protection
        await _execute_with_timeout_and_circuit_breaker(
            "update_job_status",
            lambda: anyio.to_thread.run_sync(research_service.update_job_status, job_id, "running", 5, "starting"),
            TIMEOUT_CONFIG["research_pipeline"]["memory_timeout"]
        )

        # 2. Stream the graph with enhanced timeout protection
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
            "engineered_context": {},
            "warnings": [],
            "status": "starting"
        }
        
        max_progress = 5
        _last_written_progress = 0
        pipeline_cb = PipelineLogger(job_id=job_id, session_id=session_id)
        
        # SECURITY FIX: Enhanced timeout protection with node-level monitoring
        total_timeout = TIMEOUT_CONFIG["research_pipeline"]["total_timeout"]
        node_timeout = TIMEOUT_CONFIG["research_pipeline"]["node_timeout"]
        
        try:
            async with asyncio.timeout(total_timeout):
                node_start_time = time.time()
                current_node = "unknown"
                
                async for chunk in decision_graph.astream(
                    current_state,
                    config={"callbacks": [pipeline_cb]},
                ):
                    for node_name, node_state in chunk.items():
                        current_node = node_name
                        node_duration = time.time() - node_start_time
                        
                        # SECURITY FIX: Per-node timeout monitoring
                        if node_duration > node_timeout:
                            logger.warning(f"Node {node_name} exceeded timeout ({node_duration:.1f}s > {node_timeout}s)")
                            raise TimeoutError(f"Node {node_name} timed out after {node_duration:.1f}s")
                        
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

                        # Publish to SSE event bus (non-blocking with timeout)
                        try:
                            await asyncio.wait_for(
                                bus_publish(job_id, {
                                    "status":   "running",
                                    "progress": max_progress,
                                    "step":     step_label,
                                    "node":     node_name,
                                    "meta":     meta,
                                }),
                                timeout=5  # 5 second timeout for SSE publish
                            )
                        except asyncio.TimeoutError:
                            logger.warning(f"SSE publish timed out for job {job_id}")
                        except Exception as e:
                            logger.warning(f"SSE publish failed for job {job_id}: {e}")

                        # Also update Supabase for polling fallback (throttled to >=10 point jumps)
                        if max_progress - _last_written_progress >= 10:
                            _last_written_progress = max_progress
                            try:
                                await _execute_with_timeout_and_circuit_breaker(
                                    "update_progress",
                                    lambda: anyio.to_thread.run_sync(
                                        research_service.update_job_status,
                                        job_id,
                                        "running",
                                        max_progress,
                                        step_label,
                                    ),
                                    TIMEOUT_CONFIG["research_pipeline"]["memory_timeout"]
                                )
                            except Exception as e:
                                logger.warning(f"Progress update failed (non-fatal): {e}")
                        
                        # Reset node timer for next node
                        node_start_time = time.time()
                        
        except asyncio.TimeoutError:
            error_msg = f"Research pipeline timed out after {total_timeout}s at node {current_node}"
            logger.error(error_msg)
            raise TimeoutError(error_msg)

        # Get circuit breaker stats for monitoring
        circuit_breaker_stats = circuit_manager.get_all_stats()
                
        final_state = current_state

        if final_state is None or final_state.get("status") not in {"complete", "completed"}:
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
            # SECURITY FIX: Don't expose error details in log message
            logger.warning("Failed to enqueue memory job for session %s (non-fatal)", session_id)
            logger.debug("Memory job error details: %s", e)  # Details only in debug level

        return {"session_id": session_id, "job_id": job_id, "status": "completed"}

    except Exception as exc:
        # SECURITY FIX: Enhanced error handling with circuit breaker information
        sanitized_error = _sanitize_error_message(exc, "research")
        
        # Include circuit breaker stats in logs for monitoring
        try:
            circuit_breaker_stats = circuit_manager.get_all_stats()
            breaker_status = {name: stats["state"] for name, stats in circuit_breaker_stats.items()}
            logger.error(
                "Research background task failed for job %s: %s (Circuit breakers: %s)", 
                job_id, exc, breaker_status, exc_info=True
            )
        except Exception:
            logger.error("Research background task failed for job %s: %s", job_id, exc, exc_info=True)
        
        # Write sanitized error details to DB
        try:
            await anyio.to_thread.run_sync(
                research_service.update_job_status,
                job_id,
                "failed",
                0,
                sanitized_error  # SECURITY FIX: Use sanitized error message
            )
        except Exception as db_err:
            logger.error("Failed to update job status in DB: %s", db_err)
        
        # Update session status
        try:
            await anyio.to_thread.run_sync(research_service.update_session_status, session_id, "failed")
        except Exception as session_err:
            logger.error("Failed to update session status: %s", session_err)
        
        # Publish sanitized failure event to SSE
        try:
            safe_event = _create_safe_error_event(job_id, exc, "research")
            await bus_publish(job_id, safe_event)
        except Exception as sse_err:
            logger.error("Failed to publish failure event to SSE: %s", sse_err)
        
        # DON'T re-raise — FastAPI BackgroundTasks swallows exceptions anyway
        # Return sanitized error dict for internal tracking
        return {
            "session_id": session_id, 
            "job_id": job_id, 
            "status": "failed", 
            "error": sanitized_error  # SECURITY FIX: Sanitized error in return value
        }
