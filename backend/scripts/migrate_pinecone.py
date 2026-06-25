import os
import sys
import asyncio
from typing import Dict, Any

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.config import settings
from services.pinecone_service import index as pinecone_index
from services.db import supabase

async def migrate_pinecone():
    """
    Migrates vectors from user_id namespaces to a single default namespace,
    injecting workspace_id into the metadata.
    """
    if not pinecone_index:
        print("Pinecone index not initialized. Please check your PINECONE_API_KEY.")
        return

    print("Fetching users from Supabase to find their Pinecone namespaces...")
    # Fetch distinct users from Supabase to know which namespaces to migrate
    # Or we can use Pinecone's stats to get namespaces
    try:
        stats = pinecone_index.describe_index_stats()
        namespaces = stats.get("namespaces", {})
        print(f"Found {len(namespaces)} namespaces in Pinecone.")
    except Exception as e:
        print(f"Error fetching Pinecone stats: {e}")
        return

    for user_id, ns_data in namespaces.items():
        if not user_id:
            # Skip the default namespace if it has vectors already
            continue

        print(f"Migrating namespace for user_id: {user_id} ({ns_data.get('vector_count')} vectors)")

        # Fetch the user's default workspace ("My Workspace")
        try:
            res = supabase.table("workspaces").select("id").eq("user_id", user_id).eq("name", "My Workspace").execute()
            workspace_id = res.data[0]["id"] if res.data else None
            
            if not workspace_id:
                # Fallback to any workspace owned by the user
                res = supabase.table("workspaces").select("id").eq("user_id", user_id).execute()
                workspace_id = res.data[0]["id"] if res.data else None

            if not workspace_id:
                print(f"  Warning: No workspace found for user {user_id}. Proceeding without workspace_id.")
        except Exception as e:
            print(f"  Error fetching workspace for {user_id}: {e}")
            continue

        try:
            # Query all vectors in this namespace
            # We use a dummy vector of 0s to fetch everything, but top_k is limited to 10000.
            # A better approach is to list or query all if dimensionality is known.
            # For simplicity, we assume vectors < 10000 per user for now.
            dummy_vector = [0.0] * stats.get("dimension", 1536) 
            
            query_res = pinecone_index.query(
                vector=dummy_vector,
                namespace=user_id,
                top_k=10000,
                include_values=True,
                include_metadata=True
            )
            
            matches = query_res.get("matches", [])
            print(f"  Fetched {len(matches)} vectors for {user_id}.")

            if not matches:
                continue

            # Prepare for upsert into default namespace
            vectors_to_upsert = []
            for match in matches:
                metadata = match.get("metadata", {})
                if workspace_id:
                    metadata["workspace_id"] = workspace_id
                
                vectors_to_upsert.append({
                    "id": match["id"],
                    "values": match["values"],
                    "metadata": metadata
                })

            # Upsert into default namespace
            pinecone_index.upsert(vectors=vectors_to_upsert)
            print(f"  Upserted {len(vectors_to_upsert)} vectors into default namespace.")

            # Note: We do NOT delete the old namespace here to allow manual verification first.
            print(f"  -> Please verify data. You can manually delete namespace '{user_id}' later.")

        except Exception as e:
            print(f"  Error migrating namespace {user_id}: {e}")

    print("Migration complete. Please switch the environment variable to point to the new index if needed, or verify the default namespace.")

if __name__ == "__main__":
    asyncio.run(migrate_pinecone())
