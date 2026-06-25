import asyncio
from agents.graph.decision_graph import build_decision_graph

async def main():
    graph = build_decision_graph()
    
    # We pass a complex architecture question that requires deep tradeoffs
    state = {
        "session_id": "test_session_123",
        "user_id": "test_user_123",
        "workspace_id": "test_workspace_123",
        "question": "Should we use Prisma or Drizzle ORM for our next Next.js 15 project assuming extreme performance constraints and a team used to raw SQL? The database is Postgres on Supabase.",
        "force_refresh": True,
        "warnings": [],
        "github_context": []
    }
    
    print("Running 10x Quality Harness... (This may take 15-30s due to deep reading)\n")
    try:
        # Ainvoke runs the graph asynchronously
        result = await graph.ainvoke(state)
        
        print("\n" + "="*50)
        print("REASONING SCRATCHPAD (Chain-of-Thought):")
        print("="*50)
        print(result.get("reasoning", "No reasoning found."))
        
        print("\n" + "="*50)
        print("EVIDENCE GATHERED (Uncapped & Deeply Read):")
        print("="*50)
        evidence = result.get("evidence", [])
        print(f"Total Claims Extracted: {len(evidence)}")
        for e in evidence:
            print(f"- [Trust: {e.get('trust_score', '?')}] {e.get('claim', '')} ({e.get('title', '')})")
            
        print("\n" + "="*50)
        print("FINAL RECOMMENDATION:")
        print("="*50)
        print(result.get("recommendation", ""))
        
        print("\n" + "="*50)
        print("TRADEOFFS:")
        print("="*50)
        print(result.get("tradeoffs", ""))

    except Exception as e:
        print(f"Error during execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())
