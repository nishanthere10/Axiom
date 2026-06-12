import logging
from services.db import get_supabase

logger = logging.getLogger(__name__)

def _increment_metric(column: str, amount: int = 1):
    """
    Increments a specific column in today's system_metrics_daily row.
    Supabase's REST API doesn't have a simple 'increment' operator like raw SQL, 
    so we call an RPC function. Since we might not have the RPC function,
    we'll read, increment, and upsert. In a real prod setup, you'd use a Postgres function.
    """
    try:
        supabase = get_supabase()
        
        # We need today's date in YYYY-MM-DD
        from datetime import datetime
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Fetch current
        result = supabase.table("system_metrics_daily").select("*").eq("date", today).execute()
        
        if result.data:
            current_val = result.data[0].get(column, 0)
            supabase.table("system_metrics_daily").update({
                column: current_val + amount
            }).eq("date", today).execute()
        else:
            # Create row
            supabase.table("system_metrics_daily").insert({
                "date": today,
                column: amount
            }).execute()
            
    except Exception as e:
        logger.warning(f"Failed to increment metric {column}: {e}")

def increment_research_count():
    _increment_metric("research_count")

def increment_comparison_count():
    _increment_metric("comparison_count")

def increment_fallback_count():
    _increment_metric("provider_fallback_count")

def increment_failed_memory_jobs():
    _increment_metric("failed_memory_jobs")
