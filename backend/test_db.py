from services.db import supabase
response = supabase.table("research_sessions").select("id, status, user_id, question").execute()
print("SESSIONS IN DB:")
for row in response.data:
    print(f"ID: {row['id']} | Status: {row['status']} | User: {row['user_id']} | Q: {row['question'][:20]}")
