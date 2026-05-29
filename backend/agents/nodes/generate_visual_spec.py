from typing import Any, Dict
from pydantic import BaseModel
import instructor
from groq import Groq
from api.schemas.visuals import VisualSpecResponse
from core.config import settings

def generate_visual_spec(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates relevance and conditionally generates visual specifications (up to 3).
    Returns an empty array if visuals are unnecessary.
    """
    question = state.get("question", "")
    summary = state.get("summary", "")
    recommendation = state.get("recommendation", "")
    tradeoffs = state.get("tradeoffs", "")
    alternatives = state.get("alternatives", "")
    evidence = state.get("evidence", [])
    confidence = state.get("confidence", {})
    
    # We will use the structured output format with Instructor and Groq
    client = instructor.from_groq(Groq(api_key=settings.GROQ_API_KEY))
    
    # Build a rich evidence summary for the prompt
    evidence_text = "\n".join(
        f"- [{e.get('title', 'Source')}]: {e.get('claim', '')}" for e in evidence
    ) if evidence else "No external evidence."

    prompt = f"""
    You are an expert technical architect and visual designer.
    Your task is to generate visual representations (Decision Trees, Architecture Diagrams, or Summary Cards) 
    that help clarify the following architectural decision.

    RULES:
    1. You MUST generate at least one visual if the topic involves architecture, system design, or multi-step decisions. Only return an empty array for trivial or non-technical topics.
    2. Do NOT generate more than 3 visuals.
    3. Do NOT generate duplicate visual types.
    4. For Decision Trees: Map out the conditional logic or recommendations. Include at least 4 nodes.
    5. For Architecture Diagrams: Provide valid Mermaid JS syntax. CRITICAL MERMAID SYNTAX: Never use -->|text|> for labeled arrows. You must use the standard format A -->|text| B or A -- text --> B.
       - Start with "graph TD" on the first line.
       - Use ONLY these arrow formats:
         VALID:   A --> B
         VALID:   A -->|label text| B
         VALID:   A --- B
         VALID:   A ---|label text| B
         INVALID: A -->|label text|> B   (DO NOT add > after |)
         INVALID: A -->|label text|-> B  (DO NOT add -> after |)
       - Node definitions: A[Label Text] or A{{Label Text}} or A(Label Text)
       - Do NOT use special characters like <, >, &, or quotes inside node labels.
       - Do NOT wrap in markdown code blocks.
       - Example:
         graph TD
         A[Client] -->|HTTPS| B[Load Balancer]
         B --> C[App Server]
         B --> D[App Server 2]
         C --> E[Database]
         D --> E
    6. For Summary Cards: Summarize the final recommendation, confidence, and consensus.

    QUESTION:
    {question}

    EXECUTIVE SUMMARY:
    {summary}

    RECOMMENDATION:
    {recommendation}

    TRADEOFFS:
    {tradeoffs}

    ALTERNATIVES:
    {alternatives}

    CONFIDENCE SCORES:
    {confidence}
    
    EVIDENCE:
    {evidence_text}
    """
    
    try:
        response: VisualSpecResponse = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_model=VisualSpecResponse,
            messages=[
                {"role": "system", "content": prompt}
            ]
        )
        return {"visual_specs": [v.model_dump() for v in response.visuals]}
    except Exception as e:
        print(f"Visual Generation Error: {e}")
        # Graceful fallback: return no visuals
        return {"visual_specs": []}
