from langgraph.graph import StateGraph, END
from agents.state.comparison_state import ComparisonState
from agents.nodes.load_sessions import load_sessions
from agents.nodes.normalize_documents import normalize_documents
from agents.nodes.generate_structural_diff import generate_structural_diff
from agents.nodes.generate_explanation import generate_explanation
from agents.nodes.generate_impact import generate_impact
from agents.nodes.format_comparison import format_comparison

def build_comparison_graph() -> StateGraph:
    workflow = StateGraph(ComparisonState)
    
    workflow.add_node("load_sessions", load_sessions)
    workflow.add_node("normalize_documents", normalize_documents)
    workflow.add_node("generate_structural_diff", generate_structural_diff)
    workflow.add_node("generate_explanation", generate_explanation)
    workflow.add_node("generate_impact", generate_impact)
    workflow.add_node("format_comparison", format_comparison)
    
    workflow.set_entry_point("load_sessions")
    
    workflow.add_edge("load_sessions", "normalize_documents")
    workflow.add_edge("normalize_documents", "generate_structural_diff")
    workflow.add_edge("generate_structural_diff", "generate_explanation")
    workflow.add_edge("generate_explanation", "generate_impact")
    workflow.add_edge("generate_impact", "format_comparison")
    workflow.add_edge("format_comparison", END)
    
    return workflow.compile()

comparison_graph = build_comparison_graph()
