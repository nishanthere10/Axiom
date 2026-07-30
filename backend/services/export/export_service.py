from datetime import datetime
from fastapi import HTTPException
from typing import Dict, Any

from api.schemas.export import ExportDocument, ExportSection
from services.research_service import get_document_by_session
from services.compare_service import get_comparison
from services.export.markdown_renderer import MarkdownRenderer
from services.export.adr_renderer import ADRRenderer
from services.export.pdf_renderer import PDFRenderer

def _map_research_to_export(doc: dict) -> ExportDocument:
    sections = []
    
    if doc.get("executive_summary"):
        sections.append(ExportSection(title="Executive Summary", content=doc["executive_summary"]))
    if doc.get("recommendation_context"):
        sections.append(ExportSection(title="Recommendation", content=doc["recommendation_context"]))
    if doc.get("tradeoffs"):
        sections.append(ExportSection(title="Tradeoffs", content=doc["tradeoffs"]))
    if doc.get("alternatives"):
        sections.append(ExportSection(title="Alternatives Considered", content=doc["alternatives"]))
    if doc.get("evidence"):
        ev = doc["evidence"]
        if isinstance(ev, list):
            ev_str = "\n".join([f"- {item}" for item in ev])
            sections.append(ExportSection(title="Evidence", content=ev_str))
        else:
            sections.append(ExportSection(title="Evidence", content=str(ev)))
            
    if doc.get("consensus"):
        sections.append(ExportSection(title="Consensus", content=doc["consensus"]))
    
    if doc.get("visuals") and isinstance(doc["visuals"], list):
        for idx, v in enumerate(doc["visuals"]):
            if v.get("type") == "mermaid":
                sections.append(ExportSection(
                    title=f"Visual: {v.get('title', 'Diagram')}", 
                    content=v.get("code", ""),
                    is_code=True,
                    code_language="mermaid"
                ))

    return ExportDocument(
        title=doc.get("question", "Research Decision"),
        document_type="Research Decision",
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        confidence_score=doc.get("confidence", {}).get("total_score"),
        sections=sections
    )

def _map_comparison_to_export(comp: dict) -> ExportDocument:
    sections = []
    
    if comp.get("summary"):
        sections.append(ExportSection(title="Summary", content=comp["summary"]))
        
    diff = comp.get("structural_diff", {})
    if diff.get("recommendation"):
        sections.append(ExportSection(title="Recommendation Changes", content=diff["recommendation"]))
    if diff.get("tradeoffs"):
        sections.append(ExportSection(title="Tradeoff Changes", content=diff["tradeoffs"]))
    if diff.get("alternatives"):
        sections.append(ExportSection(title="Alternatives Changes", content=diff["alternatives"]))
        
    if comp.get("visuals") and isinstance(comp["visuals"], list):
        for idx, v in enumerate(comp["visuals"]):
            if v.get("type") == "mermaid":
                sections.append(ExportSection(
                    title=f"Visual: {v.get('title', 'Diagram')}", 
                    content=v.get("code", ""),
                    is_code=True,
                    code_language="mermaid"
                ))

    return ExportDocument(
        title=f"Comparison: {comp.get('session_a', 'A')} vs {comp.get('session_b', 'B')}",
        document_type="Comparison Decision",
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        confidence_score=None,
        sections=sections
    )

def generate_export(session_type: str, session_id: str, format_type: str, user_id: str, workspace_id: str | None = None) -> tuple[bytes, str]:
    """
    Returns (file_bytes, content_type)
    """
    if session_type == "research":
        raw_doc = get_document_by_session(session_id, user_id, workspace_id)
        if not raw_doc:
            raise HTTPException(status_code=404, detail="Research session not found or unauthorized")
        export_doc = _map_research_to_export(raw_doc)
    elif session_type == "comparison":
        raw_comp = get_comparison(session_id, user_id, workspace_id)
        if not raw_comp:
            raise HTTPException(status_code=404, detail="Comparison session not found or unauthorized")
        export_doc = _map_comparison_to_export(raw_comp)
    else:
        raise HTTPException(status_code=400, detail="Invalid session type")

    if format_type == "markdown":
        renderer = MarkdownRenderer()
        return renderer.render(export_doc).encode("utf-8"), "text/markdown"
    elif format_type == "adr":
        renderer = ADRRenderer()
        return renderer.render(export_doc).encode("utf-8"), "text/markdown"
    elif format_type == "pdf":
        renderer = PDFRenderer()
        return renderer.render(export_doc), "application/pdf"
    else:
        raise HTTPException(status_code=400, detail="Invalid export format")
