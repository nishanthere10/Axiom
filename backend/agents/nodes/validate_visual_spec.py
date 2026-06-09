import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def validate_visual_spec(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the generated visual specifications.
    Ensures that unsupported types are removed, required fields are present,
    and limits the maximum number of visuals to 3.
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
                    validated_visuals.append(spec)
        except Exception as e:
            logger.warning("Skipping invalid visual spec: %s", e)
            continue

    # Rule: Max 3 visuals
    if len(validated_visuals) > 3:
        validated_visuals = validated_visuals[:3]
        
    return {"visuals": validated_visuals}
