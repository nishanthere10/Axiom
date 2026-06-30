from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import warnings
from contextlib import asynccontextmanager

from core.logging_config import configure_human_readable_logging
configure_human_readable_logging()

from api.routes.research import router as research_router
from api.routes.compare import router as compare_router
from api.routes.memory import router as memory_router
from api.routes.webhooks import router as webhooks_router
from api.routes.admin import router as admin_router
from api.routes.export import router as export_router
from api.routes.github import router as github_router
from api.routes.workspaces import router as workspaces_router
from api.routes.decisions import router as decisions_router

from middleware.rate_limit import limiter
from middleware.logging_middleware import StructlogMiddleware
from slowapi.errors import RateLimitExceeded
from core.errors import AtlasError
from services.health_service import run_all_checks
from workers.memory_sweeper import run_memory_sweeper
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the memory sweeper background task
    sweeper_task = asyncio.create_task(run_memory_sweeper())
    yield
    # Shutdown: Cancel the memory sweeper
    sweeper_task.cancel()
    try:
        await sweeper_task
    except asyncio.CancelledError:
        pass
    # Shutdown: Cleanly stop LiteLLM's internal async LoggingWorker if running.
    # Without this, uvicorn logs 'Task was destroyed but it is pending!' on every reload.
    try:
        import litellm.utils as _lu
        worker = getattr(_lu, "_logging_worker", None) or getattr(_lu, "logging_worker", None)
        if worker is not None and hasattr(worker, "_worker_loop"):
            worker_task = getattr(worker, "_task", None)
            if worker_task and not worker_task.done():
                worker_task.cancel()
                try:
                    await worker_task
                except asyncio.CancelledError:
                    pass
    except Exception:
        pass  # Non-fatal — never let cleanup crash the shutdown

app = FastAPI(
    title="Atlas Research v1 API",
    description="Backend API for Atlas Research — AI-powered engineering decision workspace.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded. Please try again later."
            }
        }
    )

@app.exception_handler(AtlasError)
async def atlas_error_handler(request: Request, exc: AtlasError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )

# CORS — allow requests from Next.js frontend (dev + prod)
import os

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://atlas-cm90ourgm-nishant-s-projects-f9ed29a6.vercel.app",
    "https://atlas-orcin-kappa.vercel.app",
    "https://atlas-1sr4.onrender.com"
]
if prod_origin := os.environ.get("FRONTEND_ORIGIN"):
    ALLOWED_ORIGINS.append(prod_origin)

app.add_middleware(StructlogMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(research_router, prefix="/research", tags=["research"])
app.include_router(compare_router, prefix="/compare", tags=["compare"])
app.include_router(memory_router, prefix="/memory", tags=["memory"])
app.include_router(webhooks_router, prefix="/webhooks", tags=["webhooks"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])
app.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
app.include_router(decisions_router, prefix="/decisions", tags=["decisions"])
app.include_router(export_router)
app.include_router(github_router)


@app.get("/health", tags=["system"])
async def health_check():
    """
    GET /health
    Returns detailed health status for all dependencies.
    Publicly accessible for system status banners and load balancers.
    """
    return await run_all_checks()

@app.get("/")
async def root_health_check():
    return {"status": "healthy", "engine": "Atlas Architectural Core"}