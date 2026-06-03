from services.llm_provider import generate_chat_completion
from core.config import settings
from agents.state.research_state import ResearchState



def decompose_question(state: ResearchState) -> dict:
    """
    Node 1: Breaks down the user's technical question into core intent,
    key concerns, and evaluation criteria. Produces the executive summary.
    """
    question = state["question"]

    response = generate_chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an elite Principal Software Architect. "
                    "A user has asked a technical research question. "
                    "Write a highly technical, dense 3-4 sentence architectural brief that: "
                    "(1) Pinpoints the exact system design or architectural decision to be made, "
                    "(2) Identifies the critical technical constraints, performance bottlenecks, or security vectors, and "
                    "(3) Outlines the exact engineering criteria that will determine the optimal solution. "
                    "Do not use generic buzzwords. Be intensely specific. Plain text only."
                ),
            },
            {
                "role": "user",
                "content": f"Technical question: {question}",
            },
        ],
        temperature=0.3,
        max_tokens=400,
    )

    summary = response.choices[0].message.content.strip()
    return {"summary": summary, "status": "decomposed"}
