import logging
from services.db import get_supabase

logger = logging.getLogger(__name__)

def _increment_metric(column: str, amount: int = 1):
    """
    Increments a specific column in today's system_metrics_daily row.
    Attempts to use an atomic RPC function first. If the RPC function does not exist,
    it falls back to a read-modify-write approach (which is susceptible to race conditions).
    """
    try:
        supabase = get_supabase()
        
        from datetime import datetime
        today = datetime.utcnow().strftime('%Y-%m-%d')
        
        # Attempt atomic RPC call
        try:
            # Assumes a Postgres function exists:
            # create or replace function increment_metric(p_date date, p_column text, p_amount int) ...
            res = supabase.rpc("increment_metric", {"p_date": today, "p_column": column, "p_amount": amount}).execute()
            return
        except Exception:
            # Fallback to read-modify-write
            pass
            
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
