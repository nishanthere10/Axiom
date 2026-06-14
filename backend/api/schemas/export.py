from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class ExportSection(BaseModel):
    title: str
    content: str
    is_code: bool = False # e.g. for mermaid blocks
    code_language: Optional[str] = None # e.g. "mermaid"

class ExportDocument(BaseModel):
    title: str
    document_type: str # e.g., "Research Decision" or "Comparison Decision"
    generated_at: str
    confidence_score: Optional[float] = None
    
    # Sections to be rendered sequentially
    sections: List[ExportSection]
    
    # Hidden metadata not printed but stored in the document logic
    metadata: Dict[str, Any] = {}
