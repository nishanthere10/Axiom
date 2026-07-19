import logging
import uuid
from typing import Dict, Any, Optional
import asyncio
from services.db import get_supabase
from services.llm_provider import generate_chat_completion
from api.schemas.memory import MemoryItemCreate
from services.memory_service import create_memory_item

logger = logging.getLogger(__name__)

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
                messages=[{"role": "system", "content": prompt}]
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
        
        # Store in Postgres (and Pinecone via the existing trigger/sweeper logic)
        def store_db():
            create_memory_item(memory_data)
            
        await asyncio.to_thread(store_db)
        logger.info(f"Successfully generated permanent memory for Decision Record {decision_record_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate memory for decision {decision_record_id}: {e}", exc_info=True)
        return False
