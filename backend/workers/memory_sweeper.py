import asyncio
import logging

from services import memory_job_service
from agents.nodes.create_memory import create_memory
from agents.nodes.store_memory import store_memory

logger = logging.getLogger(__name__)

async def process_memory_job(job: dict):
    """Processes a single memory job."""
    job_id = job["id"]
    payload = job["payload"]
    attempt_count = job["attempt_count"]
    max_attempts = job["max_attempts"]
    
    try:
        logger.info(f"Processing memory job {job_id} (attempt {attempt_count + 1})")
        # Ensure session_id, user_id, and workspace_id are passed to create_memory
        payload["session_id"] = job["session_id"]
        payload["user_id"] = job["user_id"]
        # workspace_id is stored inside payload itself (set at enqueue time)
        
        # We run the synchronous LangGraph nodes in a thread
        def run_nodes():
            memory_state = create_memory(payload)
            store_memory(memory_state)
            
        await asyncio.to_thread(run_nodes)
        
        # Success
        memory_job_service.complete_job(job_id)
        
    except Exception as e:
        error_msg = str(e)
        memory_job_service.fail_job(job_id, attempt_count, max_attempts, error_msg)

async def run_memory_sweeper():
    """
    Infinite loop that polls Postgres for pending memory jobs.
    Runs every 30 seconds. Designed to run inside the FastAPI lifespan.
    """
    logger.info("Memory sweeper started")
    while True:
        try:
            job = memory_job_service.claim_next_job()
            if job:
                # We found a job, process it immediately
                await process_memory_job(job)
                # Don't sleep if we found a job, there might be more
                continue
                
        except asyncio.CancelledError:
            logger.info("Memory sweeper cancelled")
            break
        except Exception as e:
            logger.error(f"Error in memory sweeper loop: {e}", exc_info=True)
            
        # Sleep if no jobs or if we hit an error
        await asyncio.sleep(30)
