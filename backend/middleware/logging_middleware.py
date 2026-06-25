import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars
import time

logger = structlog.get_logger(__name__)

class StructlogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Clear previous context variables to prevent leakage
        clear_contextvars()
        
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        workspace_id = request.headers.get("X-Workspace-ID", "global")
        
        # Bind context variables
        bind_contextvars(
            request_id=request_id,
            workspace_id=workspace_id,
            method=request.method,
            path=request.url.path
        )
        
        start_time = time.time()
        try:
            response = await call_next(request)
            
            # Log successful requests
            process_time = time.time() - start_time
            logger.info(
                "Request completed",
                status_code=response.status_code,
                process_time_ms=int(process_time * 1000)
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "Request failed",
                error=str(e),
                process_time_ms=int(process_time * 1000),
                exc_info=True
            )
            raise
