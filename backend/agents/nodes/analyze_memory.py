import logging
from typing import Dict, Any
from api.schemas.memory import MemoryContextSchema
from services.llm_provider import get_instructor_client

logger = logging.getLogger(__name__)

def analyze_memory(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes retrieved memories to extract preferences, patterns, and warnings.
    If no memories were retrieved, short-circuits and returns an empty context.
    """
    logger.debug("Node -> analyze_memory starting...")
    memories = state.get("retrieved_memories", [])
    github_context = state.get("github_context", [])
    
    if not memories and not github_context:
        # Short-circuit logic to save LLM calls if no context was found
        logger.debug("No memories or github context retrieved. Short-circuiting LLM analysis.")
        return {
            "memory_context": {
                "preferences": [],
                "historical_patterns": [],
                "related_decisions": [],
                "consistency_warnings": []
            }
        }
        
    question = state.get("question", "")
    if not question and "session_a_id" in state and "session_b_id" in state:
        question = f"Compare {state['session_a_id']} vs {state['session_b_id']}"
    
    # Format the memories for the LLM prompt
    formatted_memories = []
    for idx, m in enumerate(memories):
        metadata = m.get("metadata", {})
        summary = metadata.get("summary", "")
        mem_type = metadata.get("memory_type", "unknown")
        formatted_memories.append(f"Memory {idx+1} ({mem_type}): {summary}")
        
    memories_text = "\n".join(formatted_memories) if formatted_memories else "None"
    
    # Format github context
    formatted_github = []
    for chunk in github_context:
        repo = chunk.get("repository", "unknown")
        content = chunk.get("content", "")
        formatted_github.append(f"Repo: {repo}\nContext: {content}")
        
    github_text = "\n\n".join(formatted_github) if formatted_github else "None"
        
    client = get_instructor_client()
    
    prompt = f"""
    You are analyzing the user's historical architectural memories AND their current GitHub repository infrastructure context to inform a new decision.
    
    CURRENT QUESTION:
    {question}
    
    RETRIEVED MEMORIES:
    {memories_text}
    
    GITHUB REPOSITORY CONTEXT:
    {github_text}
    
    Your task is to analyze these contexts and extract:
    1. Any detected technical preferences (e.g. they prefer serverless, they like Postgres).
    2. Historical patterns (e.g. they usually choose open source).
    3. Directly related decisions or architectural rules that inform the current question.
    4. Consistency warnings (e.g. if the user is asking about NoSQL but their repo context heavily favors relational DBs, flag this).
    
    Be concise and objective.
    """
    
    try:
        logger.debug("Querying LLM to analyze memory context...")
        response: MemoryContextSchema = client.chat.completions.create(
            model="groq/llama-3.3-70b-versatile",
            response_model=MemoryContextSchema,
            max_retries=3,
            parallel_tool_calls=False,
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        logger.debug("Successfully parsed LLM memory context. Exiting node.")
        context = response.model_dump()
        context["evaluated_memories"] = memories
        context["github_context"] = github_context
        return {"memory_context": context}
    except Exception as e:
        logger.warning("Memory Analysis Error (non-fatal): %s", e)
        # Fallback to empty context on error to not crash pipeline
        return {
            "memory_context": {
                "preferences": [],
                "historical_patterns": [],
                "related_decisions": [],
                "consistency_warnings": [],
                "evaluated_memories": memories,
                "github_context": github_context
            }
        }
