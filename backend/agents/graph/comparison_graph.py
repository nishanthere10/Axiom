from langgraph.graph import StateGraph, END
from agents.state.comparison_state import ComparisonState
from agents.nodes.load_sessions import load_sessions
from agents.nodes.normalize_documents import normalize_documents
from agents.nodes.generate_structural_diff import generate_structural_diff
from agents.nodes.generate_explanation import generate_explanation
from agents.nodes.generate_impact import generate_impact
from agents.nodes.generate_comparison_visual_spec import generate_comparison_visual_spec
from agents.nodes.validate_visual_spec import validate_visual_spec
from agents.nodes.format_comparison import format_comparison
from agents.nodes.retrieve_memory import retrieve_memory
from agents.nodes.analyze_memory import analyze_memory

def build_comparison_graph() -> StateGraph:
    workflow = StateGraph(ComparisonState)
    
    workflow.add_node("load_sessions", load_sessions)
    workflow.add_node("retrieve_memory", retrieve_memory)
    workflow.add_node("analyze_memory", analyze_memory)
    workflow.add_node("normalize_documents", normalize_documents)
    workflow.add_node("generate_structural_diff", generate_structural_diff)
    workflow.add_node("generate_explanation", generate_explanation)
    workflow.add_node("generate_impact", generate_impact)
    workflow.add_node("generate_comparison_visual_spec", generate_comparison_visual_spec)
    workflow.add_node("validate_visual_spec", validate_visual_spec)
    workflow.add_node("format_comparison", format_comparison)
    
    workflow.set_entry_point("load_sessions")
    
    workflow.add_edge("load_sessions", "retrieve_memory")
    workflow.add_edge("retrieve_memory", "analyze_memory")
    workflow.add_edge("analyze_memory", "normalize_documents")
    workflow.add_edge("normalize_documents", "generate_structural_diff")
    workflow.add_edge("generate_structural_diff", "generate_explanation")
    workflow.add_edge("generate_explanation", "generate_impact")
    workflow.add_edge("generate_impact", "generate_comparison_visual_spec")
    workflow.add_edge("generate_comparison_visual_spec", "validate_visual_spec")
    workflow.add_edge("validate_visual_spec", "format_comparison")
    workflow.add_edge("format_comparison", END)
    
    return workflow.compile()

comparison_graph = build_comparison_graph()
