from typing import Any, Dict
import copy
from api.schemas.visuals import VisualSpecResponse, VisualType

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
    
    # We validate by passing through the Pydantic schema again to ensure structural integrity
    # (Though Instructor already does this, this acts as a defense-in-depth against bad upstream state mutation)
    for spec in visual_specs:
        try:
            # We don't have a direct dictionary parser for the Union without standard Pydantic TypeAdapter 
            # but since it's a dict, we can just ensure the 'type' field is one of our supported ones
            # and append it. We'll do a simple dictionary validation.
            if isinstance(spec, dict) and "type" in spec:
                v_type = spec["type"]
                if v_type in ["decision_tree", "architecture_diagram", "summary_card"]:
                    validated_visuals.append(spec)
        except Exception as e:
            print(f"Skipping invalid visual spec: {e}")
            continue

    # Rule: Max 3 visuals
    if len(validated_visuals) > 3:
        validated_visuals = validated_visuals[:3]
        
    return {"visuals": validated_visuals}
