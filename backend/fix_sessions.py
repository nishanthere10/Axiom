import os
import sys

from services.db import supabase

def fix_session_statuses():
    # Find all sessions that have a corresponding decision_document
    response = supabase.table("decision_documents").select("session_id").execute()
    session_ids = [doc["session_id"] for doc in response.data]
    
    if session_ids:
        print(f"Found {len(session_ids)} completed sessions. Updating their status...")
        for session_id in session_ids:
            supabase.table("research_sessions").update({"status": "complete"}).eq("id", session_id).execute()
        print("Updated successfully.")
    else:
        print("No completed sessions found.")

if __name__ == "__main__":
    fix_session_statuses()
