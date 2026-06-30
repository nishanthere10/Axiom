import logging
import json
from services.llm_provider import generate_chat_completion
from agents.state.research_state import ResearchState

logger = logging.getLogger(__name__)


def decompose_question(state: ResearchState) -> dict:
    """
    Node 1: Breaks down the user's technical question into core intent,
    key concerns, and evaluation criteria, as well as extracting hard constraints.
    """
    question = state["question"]

    response = generate_chat_completion(
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an elite Principal Software Architect. A user has asked a technical research question. "
                    "Break it down into two parts:\n"
                    "1. 'summary': A highly technical, dense 3-4 sentence architectural brief that pinpoints the exact system design, "
                    "critical constraints/bottlenecks, and evaluation criteria.\n"
                    "2. 'constraints': A list of hard requirements explicitly or implicitly stated (e.g. 'budget < $500', 'requires 100k writes/s', 'must be Python').\n\n"
                    "Return ONLY a JSON object with this exact schema:\n"
                    "{\n"
                    '    "summary": "The brief...",\n'
                    '    "constraints": ["constraint 1", "constraint 2"]\n'
                    "}"
                ),
            },
            {
                "role": "user",
                "content": f"Technical question: {question}",
            },
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
        max_tokens=700,
    )

    try:
        content = json.loads(response.choices[0].message.content)
        summary = content.get("summary", "Failed to decompose question.")
        constraints = content.get("constraints", [])
    except Exception as e:
        logger.error("Decomposition failed: %s", e)
        summary = "Failed to decompose question."
        constraints = []

    return {"summary": summary, "constraints": constraints, "status": "decomposed"}
