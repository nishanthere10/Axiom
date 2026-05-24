import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve the .env file relative to the backend/ root (this file's grandparent).
# This ensures it works regardless of CWD or which Python interpreter is used.
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path)

from celery import Celery

redis_url = os.getenv("REDIS_URL") or "redis://localhost:6379/0"


celery_app = Celery(
    "atlas_research_workers",
    broker=redis_url,
    backend=redis_url,
    include=["workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
