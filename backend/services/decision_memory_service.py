import logging
import uuid
from typing import Dict, Any, Optional
import asyncio
from services.db import get_supabase
from services.llm_provider import generate_chat_completion
from api.schemas.memory import MemoryItemCreate
from services.memory_service import create_memory_item
from services.pinecone_service import update_memory_metadata, upsert_memory

logger = logging.getLogger(__name__)

async def sync_decision_memory_status(decision_record_id: str, new_status: str, user_id: str):
    """
    Synchronizes decision status transitions (APPROVED, ACCEPTED, SUPERSEDED, REJECTED)
    to Supabase memory_items and Pinecone vector memory metadata.
    """
    try:
        supabase = get_supabase()
        res = supabase.table("memory_items").select("*").eq("source_id", decision_record_id).eq("source_type", "decision_record").execute()
        memories = res.data or []
        
        is_active = (new_status != "REJECTED")
        
        if memories:
            for mem in memories:
                mem_id = mem["id"]
                metadata = mem.get("metadata") or {}
                metadata["decision_status"] = new_status
                
                # Update Supabase
                supabase.table("memory_items").update({
                    "metadata": metadata,
                    "is_active": is_active,
                }).eq("id", mem_id).execute()
                
            # Update Pinecone metadata in threads concurrently
            pinecone_tasks = [
                asyncio.to_thread(
                    update_memory_metadata,
                    mem["id"],
                    {"decision_status": new_status, "is_active": is_active}
                )
                for mem in memories
            ]
            await asyncio.gather(*pinecone_tasks, return_exceptions=True)
                
            logger.info("Successfully synced memory status '%s' for decision %s", new_status, decision_record_id)
            return True
        elif new_status in ["APPROVED", "IMPLEMENTED", "ACCEPTED"]:
            # If memory doesn't exist yet for an approved decision, generate it
            return await generate_and_store_decision_memory(decision_record_id, user_id)
        else:
            logger.info("No existing memory to sync status for decision %s", decision_record_id)
            return True
    except Exception as e:
        logger.error("Failed to sync decision memory status for %s: %s", decision_record_id, e, exc_info=True)
        return False


async def generate_and_store_decision_memory(decision_record_id: str, user_id: str):
    """
    Deferred memory generation. Only called when a Decision Record is explicitly approved.
    Fetches the decision record and the underlying research report to construct the vector memory.
    """
    try:
        # Fetch decision record
        supabase = get_supabase()
        res = supabase.table("decision_records").select("*").eq("id", decision_record_id).eq("created_by", user_id).execute()
        
        if not res.data:
            logger.warning(f"Decision Record {decision_record_id} not found or unauthorized for memory generation.")
            return False
            
        record = res.data[0]
        
        # Fetch research report context
        report_res = supabase.table("research_reports").select(
            "question, recommendation_context, executive_summary"
        ).eq("session_id", record["research_session_id"]).execute()
        
        report = report_res.data[0] if report_res.data else {}
        
        question = report.get("question", "")
        recommendation = report.get("recommendation_context", "")
        
        prompt = f"""
        You are an expert technical architect compressing an APPROVED architectural decision into a retrieval-optimized memory summary.
        This summary will be embedded in a vector database to help inform future architectural decisions.
        
        DECISION TITLE: {record.get('title', '')}
        ORIGINAL QUESTION: {question}
        DECISION/RECOMMENDATION: {recommendation}
        
        Task: Write a dense, concise summary of this decision. Do not use filler words. Focus purely on technical constraints, chosen technologies, and the definitive stance taken. Maximum 3 sentences.
        """
        
        # We can run this in a thread since it's an I/O bound LLM call
        def run_llm():
            response = generate_chat_completion(
                model="groq/llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": prompt}],
                timeout=30.0,  # litellm standard timeout
            )
            return response.choices[0].message.content.strip()
            
        summary = await asyncio.to_thread(run_llm)
        
        memory_data = MemoryItemCreate(
            memory_type="decision",
            source_id=decision_record_id,
            source_type="decision_record",
            summary=summary,
            metadata={
                "decision_record_id": decision_record_id,
                "title": record.get("title"),
                "question": question,
                "summary": summary,
                "memory_type": "decision",
                "decision_status": record.get("status", "PROPOSED"),
            },
            scope="permanent", # Since it's approved, it's permanent
            user_id=user_id,
            workspace_id=record.get("workspace_id")
        )
        
        # Store in Postgres (and Pinecone vector index)
        def store_db_and_pinecone():
            pg_memory = create_memory_item(memory_data)
            if pg_memory and not pg_memory.get("_dedup_skipped"):
                memory_id = pg_memory["id"]
                pinecone_meta = memory_data.metadata.copy() if memory_data.metadata else {}
                pinecone_meta["created_at"] = pg_memory.get("created_at")
                pinecone_meta["scope"] = memory_data.scope
                pinecone_meta["user_id"] = memory_data.user_id
                upsert_memory(
                    memory_id=memory_id,
                    summary=memory_data.summary,
                    metadata=pinecone_meta,
                    workspace_id=memory_data.workspace_id
                )
            return pg_memory
            
        await asyncio.to_thread(store_db_and_pinecone)
        logger.info(f"Successfully generated permanent memory for Decision Record {decision_record_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate memory for decision {decision_record_id}: {e}", exc_info=True)
        return False

