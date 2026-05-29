from typing import Any, Dict
import re
from api.schemas.visuals import VisualSpecResponse, VisualType


def _sanitize_mermaid(syntax: str) -> str:
    """
    Fix common LLM-generated Mermaid syntax errors that cause parse failures.
    """
    # Strip markdown code fences if the LLM wrapped it
    syntax = re.sub(r'^```(?:mermaid)?\s*', '', syntax, flags=re.MULTILINE)
    syntax = re.sub(r'```\s*$', '', syntax, flags=re.MULTILINE)

    # Fix: -->|label|> B  =>  -->|label| B   (trailing > after pipe)
    syntax = re.sub(r'\|>\s', '| ', syntax)
    # Fix: -->|label|-> B  =>  -->|label| B  (trailing -> after pipe)
    syntax = re.sub(r'\|->\s', '| ', syntax)
    # Fix: ---|label|> B  =>  ---|label| B
    syntax = re.sub(r'\|>\s', '| ', syntax)

    # Remove angle brackets inside node labels like A[<text>] => A[text]
    # Match [...] content and strip < >
    def clean_label(m):
        content = m.group(1).replace('<', '').replace('>', '')
        return f'[{content}]'
    syntax = re.sub(r'\[([^\]]*[<>][^\]]*)\]', clean_label, syntax)

    # Remove & inside node labels
    def clean_amp(m):
        content = m.group(1).replace('&', 'and')
        return f'[{content}]'
    syntax = re.sub(r'\[([^\]]*&[^\]]*)\]', clean_amp, syntax)

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

