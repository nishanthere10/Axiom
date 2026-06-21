from services.db import supabase

response = supabase.table("decision_documents").select("memory_context").limit(1).execute()
print(response.data)
