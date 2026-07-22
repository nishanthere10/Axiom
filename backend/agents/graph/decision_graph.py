from langgraph.graph import StateGraph, START, END
from agents.state.research_state import ResearchState
from agents.nodes.decompose import decompose_question
from agents.nodes.canonicalize_topic import canonicalize_topic
from agents.nodes.generate_queries import generate_queries
from agents.nodes.collect_and_score_evidence import collect_and_score_evidence
from agents.nodes.assemble_context import assemble_context
from agents.nodes.generate import generate_decision
from agents.nodes.confidence import build_confidence
from agents.nodes.generate_visual_spec import generate_visual_spec
from agents.nodes.validate_visual_spec import validate_visual_spec
from agents.nodes.retrieve_memory import retrieve_memory
from agents.nodes.memory_relevance_evaluator import memory_relevance_evaluator
from agents.nodes.analyze_memory import analyze_memory
from agents.nodes.format import format_document
from agents.nodes.retrieve_github_context import retrieve_github_context
from agents.nodes.context_relevance_scorer import context_relevance_scorer

def build_decision_graph():
    """
    Compiles the LangGraph decision pipeline.
    """
    graph = StateGraph(ResearchState)

    # Register nodes
    graph.add_node("decompose_question", decompose_question)
    graph.add_node("retrieve_memory", retrieve_memory)
    graph.add_node("memory_relevance_evaluator", memory_relevance_evaluator)
    graph.add_node("retrieve_github_context", retrieve_github_context)
    graph.add_node("analyze_memory", analyze_memory)
    graph.add_node("canonicalize_topic", canonicalize_topic)
    graph.add_node("generate_queries", generate_queries)
    graph.add_node("collect_and_score_evidence", collect_and_score_evidence)
    graph.add_node("assemble_context", assemble_context)
    graph.add_node("generate_decision", generate_decision)
    graph.add_node("build_confidence", build_confidence)
    graph.add_node("generate_visual_spec", generate_visual_spec)
    graph.add_node("validate_visual_spec", validate_visual_spec)
    graph.add_node("format_document", format_document)
    graph.add_node("context_relevance_scorer", context_relevance_scorer)

    # Wire edges
    # Phase 1: Parallel initial data gathering
    graph.add_edge(START, "decompose_question")
    graph.add_edge(START, "retrieve_memory")
    graph.add_edge(START, "canonicalize_topic")

    # GitHub retrieval now waits for decomposed intent before searching
    graph.add_edge("decompose_question", "retrieve_github_context")

    # Phase 2: Analyze memory and generate queries
    graph.add_edge("retrieve_memory", "memory_relevance_evaluator")
    # analyze_memory waits for: memory relevance eval + targeted github context
    graph.add_edge(["memory_relevance_evaluator", "retrieve_github_context"], "analyze_memory")
    graph.add_edge("decompose_question", "generate_queries")

    # Phase 3: Wait for both queries and memory to collect evidence
    graph.add_edge("analyze_memory", "context_relevance_scorer")
    graph.add_edge([
        "generate_queries",
        "context_relevance_scorer"
    ], "collect_and_score_evidence")
    
    # Phase 4: Context assembly & decision generation
    graph.add_edge("collect_and_score_evidence", "assemble_context")
    graph.add_edge("assemble_context", "generate_decision")
    
    # Phase 5: Parallel post-decision processing
    graph.add_edge("generate_decision", "build_confidence")
    graph.add_edge("generate_decision", "generate_visual_spec")
    
    # Phase 6: Visual validation
    graph.add_edge("generate_visual_spec", "validate_visual_spec")
    
    # Phase 7: Wait for all post-processing to format the final document
    # NOTE: canonicalize_topic is NOT included here — it runs at START (parallel)
    # and its output is accumulated to state by tasks.py. Including it in a fan-in
    # with late-running nodes causes LangGraph to stall waiting for a node that
    # already completed and was cleared from the pending-node tracker.
    graph.add_edge(["build_confidence", "validate_visual_spec"], "format_document")
    
    graph.add_edge("format_document", END)

    return graph.compile()

# Compiled graph instance — imported by FastAPI background tasks
decision_graph = build_decision_graph()
