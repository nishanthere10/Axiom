from groq import Groq
from core.config import settings
from agents.state.research_state import ResearchState

_client = Groq(api_key=settings.GROQ_API_KEY)
_MODEL = "llama-3.3-70b-versatile"


def decompose_question(state: ResearchState) -> dict:
    """
    Node 1: Breaks down the user's technical question into core intent,
    key concerns, and evaluation criteria. Produces the executive summary.
    """
    question = state["question"]

    response = _client.chat.completions.create(
        model=_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a senior software architect. "
                    "A user has asked a technical research question. "
                    "Write a clear 2-3 sentence executive summary that: "
                    "(1) restates the core decision to be made, "
                    "(2) identifies the key technical concerns, and "
                    "(3) outlines what factors will determine the right answer. "
                    "Be direct. No markdown. Plain text only."
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
