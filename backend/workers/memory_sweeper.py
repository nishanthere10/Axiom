import asyncio
import logging
import time

from services import memory_job_service
from agents.nodes.create_memory import create_memory
from agents.nodes.store_memory import store_memory
from services.circuit_breaker import circuit_manager

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Exponential Backoff Configuration
# ─────────────────────────────────────────────────────────────────────────────
# Used when database errors occur to prevent tight CPU loop spam

class BackoffTracker:
    """Tracks exponential backoff state for database errors."""
    
    def __init__(self):
        self.error_count = 0
        self.base_delay_seconds = 5  # Start with 5 seconds
        self.max_delay_seconds = 300  # Cap at 5 minutes
        self.multiplier = 2.0
        
    def get_delay(self) -> float:
        """Calculate exponential backoff delay."""
        delay = min(
            self.base_delay_seconds * (self.multiplier ** self.error_count),
            self.max_delay_seconds
        )
        return delay
    
    def record_error(self) -> None:
        """Record an error and increase backoff."""
        self.error_count = min(self.error_count + 1, 10)  # Cap at 10 to prevent overflow
        
    def record_success(self) -> None:
        """Reset backoff after successful operation."""
        self.error_count = 0

async def process_memory_job(job: dict):
    """
    Processes a single memory job with circuit breaker protection.
    
    SECURITY FIX: Added timeout and circuit breaker protection.
    
    Args:
        job: Memory job dict from database
        
    Raises:
        Exception: Re-raised after logging to signal sweeper to backoff
    """
    job_id = job["id"]
    payload = job["payload"]
    attempt_count = job["attempt_count"]
    max_attempts = job.get("max_attempts", 3)
    
    try:
        logger.info(f"Processing memory job {job_id} (attempt {attempt_count + 1}/{max_attempts})")
        
        # Ensure required fields are passed to create_memory
        payload["session_id"] = job["session_id"]
        payload["user_id"] = job["user_id"]
        # workspace_id is stored inside payload itself (set at enqueue time)
        
        # Use circuit breaker for memory processing
        breaker = circuit_manager.get_breaker(
            "memory_processing",
            failure_threshold=2,
            failure_rate_threshold=0.5,
            recovery_timeout=120,  # 2 minutes
            timeout=60  # 1 minute per memory job
        )
        
        # Run the synchronous LangGraph nodes with timeout protection
        def run_nodes():
            memory_state = create_memory(payload)
            store_memory(memory_state)
        
        await breaker.call(asyncio.to_thread.run_sync, run_nodes)
        
        # Success - mark job as completed
        memory_job_service.complete_job(job_id)
        logger.info(f"✓ Memory job {job_id} completed successfully")
        
    except Exception as e:
        error_msg = str(e)[:200]  # Truncate error message
        logger.error(f"Memory job {job_id} failed: {error_msg}", exc_info=True)
        
        try:
            memory_job_service.fail_job(job_id, attempt_count, max_attempts, error_msg)
        except Exception as fail_err:
            logger.error(f"Failed to update job {job_id} status: {fail_err}")

async def run_memory_sweeper():
    """
    PRODUCTION FIX: Infinite loop that polls for pending memory jobs.
    
    IMPROVEMENTS:
      1. Catches database errors without crashing
      2. Implements exponential backoff when errors occur
      3. Rapid polling when jobs are found (no artificial sleep)
      4. Graceful shutdown on CancelledError
      5. Detailed logging for observability
    
    BEHAVIOR:
      - If job found → process immediately, loop continues (no sleep)
      - If no job found → sleep 30 seconds
      - If database error → exponential backoff (5s → 10s → 20s ... → 300s max)
      - After error resolves → backoff resets
      - On CancelledError → graceful shutdown
    
    EXECUTION:
      Run this in FastAPI lifespan:
      
      async def lifespan(app):
          task = asyncio.create_task(run_memory_sweeper())
          yield
          task.cancel()
          
      app = FastAPI(lifespan=lifespan)
    """
    
    logger.info("=" * 80)
    logger.info("Memory sweeper started")
    logger.info("=" * 80)
    
    backoff = BackoffTracker()
    consecutive_errors = 0
    
    while True:
        try:
            # ─────────────────────────────────────────────────────────────────
            # ATTEMPT: Claim and process next job
            # ─────────────────────────────────────────────────────────────────
            try:
                job = memory_job_service.claim_next_job()
                
                if job:
                    # Job found - process immediately
                    logger.debug(f"Found job {job['id']}, processing immediately")
                    
                    try:
                        await process_memory_job(job)
                        consecutive_errors = 0
                        backoff.record_success()
                        logger.debug("Job processed, continuing loop without sleep")
                        continue  # Don't sleep, there might be more jobs
                    except Exception as process_err:
                        consecutive_errors += 1
                        logger.warning(
                            f"Memory job processing error (attempt {consecutive_errors}): {process_err}"
                        )
                        # Continue to sleep logic below
                else:
                    # No jobs found - normal operation
                    logger.debug("No pending jobs found")
                    consecutive_errors = 0
                    backoff.record_success()
                    
            except Exception as claim_err:
                # Database error during job claiming
                consecutive_errors += 1
                backoff.record_error()
                
                error_type = type(claim_err).__name__
                error_str = str(claim_err).lower()
                
                # Categorize the error for logging
                if "pgrst202" in error_str or "function" in error_str:
                    logger.error(
                        f"Database error (PGRST202 - RPC not found): {claim_err} "
                        f"[Attempt {consecutive_errors}] [Backing off for {backoff.get_delay():.1f}s]"
                    )
                elif "42703" in error_str or "column" in error_str:
                    logger.error(
                        f"Database error (42703 - Column not found): {claim_err} "
                        f"[Attempt {consecutive_errors}] [Backing off for {backoff.get_delay():.1f}s]"
                    )
                elif "connection" in error_str or "network" in error_str:
                    logger.error(
                        f"Database error (Connection): {claim_err} "
                        f"[Attempt {consecutive_errors}] [Backing off for {backoff.get_delay():.1f}s]"
                    )
                else:
                    logger.error(
                        f"Database error ({error_type}): {claim_err} "
                        f"[Attempt {consecutive_errors}] [Backing off for {backoff.get_delay():.1f}s]"
                    )
            
            # ─────────────────────────────────────────────────────────────────
            # SLEEP LOGIC
            # ─────────────────────────────────────────────────────────────────
            # Determine sleep duration based on state
            
            if consecutive_errors > 0:
                # Database error occurred - use exponential backoff
                sleep_duration = backoff.get_delay()
                logger.warning(
                    f"Exponential backoff activated: sleeping for {sleep_duration:.1f}s "
                    f"(error count: {consecutive_errors})"
                )
            else:
                # Normal operation - sleep for standard poll interval
                sleep_duration = 30
                logger.debug(f"No jobs or errors - sleeping for {sleep_duration}s")
            
            # Sleep with asyncio to allow cancellation
            await asyncio.sleep(sleep_duration)
            
        except asyncio.CancelledError:
            # Graceful shutdown
            logger.info("Memory sweeper received cancellation signal, shutting down gracefully")
            break
            
        except Exception as unexpected_err:
            # Unexpected error - log and continue with backoff
            logger.exception(f"Unexpected error in memory sweeper: {unexpected_err}")
            consecutive_errors += 1
            backoff.record_error()
            sleep_duration = backoff.get_delay()
            logger.warning(f"Unexpected error backoff: sleeping for {sleep_duration:.1f}s")
            
            try:
                await asyncio.sleep(sleep_duration)
            except asyncio.CancelledError:
                logger.info("Cancelled during error recovery sleep")
                break
    
    logger.info("=" * 80)
    logger.info("Memory sweeper stopped")
    logger.info("=" * 80)

