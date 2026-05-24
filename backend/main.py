from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.research import router as research_router

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


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok", "service": "atlas-research-api", "version": "1.0.0"}

