from api.schemas.export import ExportDocument

class MarkdownRenderer:
    def render(self, doc: ExportDocument) -> str:
        lines = []
        lines.append(f"# {doc.title}")
        lines.append(f"**Generated:** {doc.generated_at}")
        if doc.confidence_score is not None:
            lines.append(f"**Confidence Score:** {doc.confidence_score:.2f}/10")
        lines.append("")
        
        for section in doc.sections:
            lines.append(f"## {section.title}")
            if section.is_code:
                lang = section.code_language or ""
                lines.append(f"```{lang}\n{section.content}\n```")
            else:
                lines.append(section.content)
            lines.append("")
            
        return "\n".join(lines)
