import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from services.db import supabase

def check_jobs():
    print("Checking github_sync_jobs table:")
    res = supabase.table("github_sync_jobs").select("*").order("created_at", desc=True).limit(5).execute()
    for job in res.data:
        print(f"Job ID: {job['id']}, Status: {job['status']}, Repo: {job['repository_id']}, Created: {job['created_at']}")

if __name__ == "__main__":
    check_jobs()
