from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import warnings

# Suppress annoying litellm/asyncio warnings about unawaited coroutines and pending tasks
warnings.filterwarnings("ignore", message="Task was destroyed but it is pending!", category=RuntimeWarning)
warnings.filterwarnings("ignore", message=".*was never awaited.*", category=RuntimeWarning)

from api.routes.research import router as research_router
from api.routes.compare import router as compare_router
from api.routes.memory import router as memory_router

app = FastAPI(
    title="Atlas Research v1 API",
    description="Backend API for Atlas Research — AI-powered engineering decision workspace.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow requests from Next.js frontend (dev + prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",  # production Vercel deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(research_router, prefix="/research", tags=["research"])
app.include_router(compare_router, prefix="/compare", tags=["compare"])
app.include_router(memory_router, prefix="/memory", tags=["memory"])


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "service": "atlas-research-api", "version": "1.0.0"}

