from celery import Task
from workers.celery_app import celery_app
from agents.graph.decision_graph import decision_graph
from services import research_service

# Progress milestones per node (used when streaming the graph)
_NODE_PROGRESS = {
    "decompose_question": (10, 25),
    "generate_decision": (25, 60),
    "build_confidence": (60, 85),
    "format_document": (85, 100),
}


@celery_app.task(
    bind=True,
    name="workers.tasks.run_research_task",
    max_retries=2,
    default_retry_delay=5,
)
def run_research_task(self: Task, session_id: str, job_id: str, question: str) -> dict:
    """
    Celery task that runs the LangGraph decision pipeline.

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
        final_state = None
        for chunk in decision_graph.stream({"question": question, "summary": "", "recommendation": "", "tradeoffs": "", "alternatives": "", "confidence": {}, "status": "starting"}):
            for node_name, node_state in chunk.items():
                _, progress = _NODE_PROGRESS.get(node_name, (0, 0))
                research_service.update_job_status(
                    job_id,
                    status="running",
                    progress=progress,
                    step=node_name,
                )
                final_state = node_state

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

        return {"session_id": session_id, "job_id": job_id, "status": "completed"}

    except Exception as exc:
        # Retry on timeout / transient errors (not on validation errors)
        is_transient = isinstance(exc, (TimeoutError, ConnectionError))
        research_service.update_job_status(job_id, status="failed", progress=0, step="error")
        research_service.update_session_status(session_id, "failed")

        if is_transient and self.request.retries < self.max_retries:
            raise self.retry(exc=exc)

        raise
