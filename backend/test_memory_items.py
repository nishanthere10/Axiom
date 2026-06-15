from services.db import supabase

try:
    response = supabase.table("memory_items").select("id").limit(1).execute()
    print("memory_items table exists!")
except Exception as e:
    print(f"Error querying memory_items: {e}")
