from langgraph.graph import StateGraph, START, END
from agents.state.research_state import ResearchState
from agents.nodes.decompose import decompose_question
from agents.nodes.generate import generate_decision
from agents.nodes.confidence import build_confidence
from agents.nodes.format import format_document


def build_decision_graph():
    """
    Compiles the LangGraph decision pipeline.

    Flow: START → decompose_question → generate_decision → build_confidence → format_document → END
    No extra nodes. Linear execution only.
    """
    graph = StateGraph(ResearchState)

    # Register nodes
    graph.add_node("decompose_question", decompose_question)
    graph.add_node("generate_decision", generate_decision)
    graph.add_node("build_confidence", build_confidence)
    graph.add_node("format_document", format_document)

    # Wire edges — strict linear order
    graph.add_edge(START, "decompose_question")
    graph.add_edge("decompose_question", "generate_decision")
    graph.add_edge("generate_decision", "build_confidence")
    graph.add_edge("build_confidence", "format_document")
    graph.add_edge("format_document", END)

    return graph.compile()


# Compiled graph instance — imported by FastAPI background tasks
decision_graph = build_decision_graph()
