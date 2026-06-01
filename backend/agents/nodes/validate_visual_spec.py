from typing import Any, Dict
import re
from api.schemas.visuals import VisualSpecResponse, VisualType


def _sanitize_mermaid(syntax: str) -> str:
    """
    Fix common LLM-generated Mermaid syntax errors that cause parse failures.
    This is the backend defense layer — the frontend has its own sanitizer too.
    """
    # Strip markdown code fences if the LLM wrapped it
    syntax = re.sub(r'^```(?:mermaid)?\s*', '', syntax, flags=re.MULTILINE)
    syntax = re.sub(r'```\s*$', '', syntax, flags=re.MULTILINE)
    syntax = syntax.strip()

    # Remove trailing periods, commas, semicolons at the end of any line
    # e.g. "E --> F[Target System]." → "E --> F[Target System]"
    syntax = re.sub(r'([^\s])[.,;]+\s*$', r'\1', syntax, flags=re.MULTILINE)

    # Fix: -->|label|> B  =>  -->|label| B   (trailing > after pipe)
    syntax = re.sub(r'\|>\s', '| ', syntax)
    # Fix: -->|label|-> B  =>  -->|label| B  (trailing -> after pipe)
    syntax = re.sub(r'\|->\s', '| ', syntax)

    # Quote node labels containing special characters that break Mermaid
    # A[Label (Extra Info)] → A["Label (Extra Info)"]
    def quote_special_labels(m):
        content = m.group(1)
        # Already quoted — leave alone
        if content.startswith('"') and content.endswith('"'):
            return f'[{content}]'
        # Contains parentheses, angle brackets, ampersands, or HTML
        if re.search(r'[()<>&;#{}]', content):
            escaped = content.replace('"', "'")
            return f'["{escaped}"]'
        return m.group(0)
    syntax = re.sub(r'\[([^\]]+)\]', quote_special_labels, syntax)

    # Remove HTML tags inside labels: A[<b>Text</b>] → A["Text"]
    def strip_html_labels(m):
        content = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        return f'["{content}"]'
    syntax = re.sub(r'\[([^\]]*<[^>]+>[^\]]*)\]', strip_html_labels, syntax)

    # Ensure the diagram starts with a valid directive
    lines = syntax.split('\n')
    first_content_line = next((l.strip() for l in lines if l.strip()), '')
    valid_starters = re.compile(
        r'^(graph|flowchart|sequenceDiagram|classDiagram|stateDiagram|erDiagram|gantt|pie|gitGraph|mindmap|timeline|journey|%%)',
        re.IGNORECASE
    )
    if not valid_starters.match(first_content_line):
        syntax = 'graph TD\n' + syntax

    return syntax.strip()



def validate_visual_spec(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the generated visual specifications.
    Ensures that unsupported types are removed, required fields are present,
    sanitizes Mermaid syntax, and limits the maximum number of visuals to 3.
    """
    visual_specs = state.get("visual_specs", [])
    
    if not isinstance(visual_specs, list):
        return {"visuals": []}

    validated_visuals = []
    
    for spec in visual_specs:
        try:
            if isinstance(spec, dict) and "type" in spec:
                v_type = spec["type"]
                if v_type in ["decision_tree", "architecture_diagram", "summary_card"]:
                    # Sanitize Mermaid syntax for architecture diagrams
                    if v_type == "architecture_diagram" and "mermaid_syntax" in spec:
                        spec["mermaid_syntax"] = _sanitize_mermaid(spec["mermaid_syntax"])
                    validated_visuals.append(spec)
        except Exception as e:
            print(f"Skipping invalid visual spec: {e}")
            continue

    # Rule: Max 3 visuals
    if len(validated_visuals) > 3:
        validated_visuals = validated_visuals[:3]
        
    return {"visuals": validated_visuals}

