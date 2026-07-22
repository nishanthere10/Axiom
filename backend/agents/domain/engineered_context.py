from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class EngineeredContext(BaseModel):
    """
    Unified context domain model representing evaluated, prioritized, 
    and structured engineering knowledge for LLM reasoning.
    """
    memory_text: str = Field(default="", description="Formatted historical memories and user preferences")
    evidence_text: str = Field(default="", description="Formatted and scored external web evidence")
    github_text: str = Field(default="", description="Formatted repository code context and architecture blueprint")
    warnings: List[str] = Field(default_factory=list, description="Active consistency or architectural warnings")
    sources: List[Dict[str, Any]] = Field(default_factory=list, description="Structured source references for citation tracking")

    def to_prompt_dict(self) -> Dict[str, str]:
        return {
            "memory_text": self.memory_text or "No memory context.",
            "evidence_text": self.evidence_text or "No external evidence provided.",
            "github_text": self.github_text or "No repository context provided.",
            "warnings_text": "\n".join(f"- ⚠️ {w}" for w in self.warnings) if self.warnings else "None."
        }
