from services.db import supabase
import sys

try:
    print("Trying to fetch memory_context...")
    response = supabase.table("decision_documents").select("id, memory_context").limit(1).execute()
    print("Success:", response.data)
except Exception as e:
    print("Error:", e)
    
sys.exit(0)
