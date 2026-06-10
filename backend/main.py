from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import warnings
from contextlib import asynccontextmanager

from core.logging_config import configure_human_readable_logging
configure_human_readable_logging()

from api.routes.research import router as research_router
from api.routes.compare import router as compare_router
from api.routes.memory import router as memory_router
from api.routes.webhooks import router as webhooks_router

app = FastAPI(
    title="Atlas Research v1 API",
    description="Backend API for Atlas Research — AI-powered engineering decision workspace.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow requests from Next.js frontend (dev + prod)
import os

ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
if prod_origin := os.environ.get("FRONTEND_ORIGIN"):
    ALLOWED_ORIGINS.append(prod_origin)

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


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "service": "atlas-research-api", "version": "1.0.0"}

