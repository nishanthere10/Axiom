import io
import logging
import re
from xml.sax.saxutils import escape
from fastapi import HTTPException
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from api.schemas.export import ExportDocument

logger = logging.getLogger(__name__)

def escape_xml(text: str) -> str:
    """Escapes special characters for ReportLab XML parser."""
    if not text:
        return ""
    return escape(text)

def format_markdown_text(text: str) -> str:
    """Basic conversion of markdown text to ReportLab Paragraph XML."""
    if not text:
        return ""
    
    # 1. Normalize line endings and escape XML characters first
    text = text.replace('\r', '')
    text = escape_xml(text)
    
    # 2. Bold: **text**
    # Using negative lookbehinds/lookaheads to avoid matching list items or stray asterisks
    text = re.sub(r'\*\*(?!\s)(.*?)(?<!\s)\*\*', r'<b>\1</b>', text)
    
    # 3. Italic: *text* 
    text = re.sub(r'\*(?!\s)(.*?)(?<!\s)\*', r'<i>\1</i>', text)
    
    # 4. Newlines to <br/>
    text = text.replace('\n', '<br/>')
    
    return text

class PDFRenderer:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        
        # Add custom style if Code is not perfect, but usually getSampleStyleSheet has 'Code'
        if 'Code' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='Code',
                parent=self.styles['Normal'],
                fontName='Courier',
                fontSize=9,
                leading=11,
                backColor='#f6f8fa',
                borderColor='#e1e4e8',
                borderWidth=1,
                borderPadding=5,
                borderRadius=3
            ))

    def render(self, doc: ExportDocument) -> bytes:
        try:
            buffer = io.BytesIO()
            doc_template = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            elements = []
            
            # Title
            elements.append(Paragraph(escape_xml(doc.title), self.styles['Title']))
            elements.append(Spacer(1, 12))
            
            # Metadata
            elements.append(Paragraph(f"<b>Generated:</b> {escape_xml(doc.generated_at)}", self.styles['Normal']))
            if doc.confidence_score is not None:
                elements.append(Paragraph(f"<b>Confidence Score:</b> {doc.confidence_score:.2f}/10", self.styles['Normal']))
            elements.append(Spacer(1, 24))

            # Sections
            for section in doc.sections:
                elements.append(Paragraph(escape_xml(section.title), self.styles['Heading2']))
                elements.append(Spacer(1, 12))
                
                if section.is_code:
                    # Render as code block with correctly escaped XML chars
                    code_text = escape_xml(section.content)
                    elements.append(Preformatted(code_text, self.styles['Code']))
                else:
                    # For basic markdown, split by double newline to create paragraphs.
                    # This prevents one massive paragraph block and preserves intended spacing.
                    paragraphs = section.content.split('\n\n')
                    for p in paragraphs:
                        p_text = format_markdown_text(p)
                        if p_text.strip():
                            elements.append(Paragraph(p_text, self.styles['Normal']))
                            elements.append(Spacer(1, 6))

                elements.append(Spacer(1, 12))

            if not elements:
                elements.append(Paragraph("Empty Document", self.styles['Normal']))

            doc_template.build(elements)
            return buffer.getvalue()
        except Exception as e:
            logger.error(f"Error rendering PDF with ReportLab: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to render PDF: {str(e)}"
            )
