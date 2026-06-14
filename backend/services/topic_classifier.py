import logging
from enum import Enum
from pydantic import BaseModel, Field
from services.llm_provider import get_instructor_client
from services.metrics_service import emit_event

logger = logging.getLogger(__name__)

class TopicLabel(str, Enum):
    AI_AGENTS = "AI Agents"
    VECTOR_DATABASES = "Vector Databases"
    CLOUD = "Cloud"
    BACKEND = "Backend"
    FRONTEND = "Frontend"
    SYSTEM_DESIGN = "System Design"
    ARCHITECTURE = "Architecture"
    OPEN_SOURCE = "Open Source"
    OTHER = "Other"

class TopicClassification(BaseModel):
    topic: TopicLabel = Field(description="The most appropriate topic label for the user's research query.")

def classify_topic_background(query: str, user_id: str = None):
    """
    Background worker function to classify a user's research query into a predefined topic
    and emit the analytics event. 
    Crucially, it drops the raw query from memory after classification.
    """
    try:
        client = get_instructor_client()
        
        # We classify without keeping the query anywhere
        response: TopicClassification = client.chat.completions.create(
            model="groq/llama-3.3-70b-versatile",
            response_model=TopicClassification,
            messages=[
                {"role": "system", "content": "You are a data classification assistant. Classify the user's technical research query into exactly one of the provided topics. Choose 'Other' if it doesn't clearly fit."},
                {"role": "user", "content": query}
            ]
        )
        
        # Emit the event with ONLY the enum value, NOT the query
        emit_event(
            event_type="topic_classified",
            metadata={"topic": response.topic.value},
            user_id=user_id
        )
        logger.debug(f"Query classified as topic: {response.topic.value}")
        
    except Exception as e:
        logger.warning(f"Failed to classify topic for query: {e}")
