import logging
from typing import Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

STATUS_WEIGHTS = {
    "ACCEPTED": 1.2,
    "APPROVED": 1.2,
    "IMPLEMENTED": 1.2,
    "PROPOSED": 1.0,
    "ARCHIVED": 0.3,
    "SUPERSEDED": 0.3,
    "REJECTED": 0.1,
}

def _parse_timestamp(ts_val) -> float:
    """Returns age in days from a timestamp string or object."""
    if not ts_val:
        return 0.0
    try:
        if isinstance(ts_val, (int, float)):
            dt = datetime.fromtimestamp(ts_val, tz=timezone.utc)
        elif isinstance(ts_val, str):
            clean_ts = ts_val.rstrip("Z")
            dt = datetime.fromisoformat(clean_ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        else:
            return 0.0
            
        now = datetime.now(timezone.utc)
        age = (now - dt).total_seconds() / 86400.0
        return max(0.0, age)
    except Exception:
        return 0.0


def memory_relevance_evaluator(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Multi-factor memory scoring for retrieved memories:
    - Pinned memories get score 1.0.
    - Decision status weights (ACCEPTED: 1.2x, PROPOSED: 1.0x, SUPERSEDED: 0.3x, REJECTED: 0.1x).
    - Temporal decay factor over time.
    """
    logger.debug("Node -> memory_relevance_evaluator starting...")
    memories = state.get("retrieved_memories", [])
    
    if not memories:
        logger.debug("No memories to evaluate.")
        return {"retrieved_memories": []}
        
    evaluated_memories = []
    for memory in memories:
        if "metadata" not in memory:
            memory["metadata"] = {}
        metadata = memory["metadata"]
        
        if metadata.get("pinned", False) or metadata.get("is_pinned", False):
            metadata["relevance_score"] = 1.0
            metadata["relevance_reasoning"] = "Pinned by user"
            evaluated_memories.append(memory)
            continue

        raw_score = float(memory.get("score") if memory.get("score") is not None else 1.0)
        status = str(metadata.get("decision_status") or metadata.get("status") or "").upper()
        status_weight = STATUS_WEIGHTS.get(status, 1.0)

        ts = metadata.get("created_at") or metadata.get("timestamp") or memory.get("created_at")
        age_in_days = _parse_timestamp(ts)
        decay_factor = max(0.2, 1.0 / (1.0 + (age_in_days / 90.0)))

        multi_factor_score = min(1.0, max(0.0, raw_score * status_weight * decay_factor))
        metadata["relevance_score"] = round(multi_factor_score, 4)
        metadata["relevance_reasoning"] = (
            f"Base: {raw_score:.2f}, status: {status_weight}x ({status or 'UNSPECIFIED'}), "
            f"decay: {decay_factor:.2f} ({int(age_in_days)}d)"
        )
        evaluated_memories.append(memory)

    # Sort best-scoring memories first
    evaluated_memories.sort(key=lambda m: m.get("metadata", {}).get("relevance_score", 0.0), reverse=True)

    # Drop effectively-zero scored memories (REJECTED + old, or truly irrelevant)
    SCORE_FLOOR = 0.05
    filtered = [m for m in evaluated_memories if m.get("metadata", {}).get("relevance_score", 0.0) >= SCORE_FLOOR]
    dropped_count = len(evaluated_memories) - len(filtered)
    if dropped_count:
        logger.debug("memory_relevance_evaluator: dropped %d memories below score floor %.2f", dropped_count, SCORE_FLOOR)

    return {"retrieved_memories": filtered}

