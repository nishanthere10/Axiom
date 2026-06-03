import os
import litellm
import instructor
from litellm import completion
from core.config import settings
from typing import Any, Dict, List, Optional

# Pre-configure environment variables for litellm based on our settings
os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
if settings.GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
if settings.MISTRAL_API_KEY:
    os.environ["MISTRAL_API_KEY"] = settings.MISTRAL_API_KEY
if settings.NVIDIA_API_KEY:
    os.environ["NVIDIA_API_KEY"] = settings.NVIDIA_API_KEY

def _build_fallbacks() -> List[Dict[str, str]]:
    """Builds a dynamic list of fallback models based on available API keys."""
    fallbacks = []
    
    # Priority 1: Gemini
    if settings.GEMINI_API_KEY:
        fallbacks.append({"model": "gemini/gemini-1.5-pro"})
        
    # Priority 2: Mistral
    if settings.MISTRAL_API_KEY:
        fallbacks.append({"model": "mistral/mistral-large-latest"})
        
    # Priority 3: NVIDIA
    if settings.NVIDIA_API_KEY:
        # Example nvidia model, replace with your preferred model
        fallbacks.append({"model": "nvidia_nim/meta/llama3-70b-instruct"})
        
    return fallbacks

def generate_chat_completion(messages: List[Dict[str, str]], model: str = "groq/llama-3.3-70b-versatile", **kwargs) -> Any:
    """
    Unified LLM chat completion with automatic fallback routing.
    If the primary model (Groq) hits a rate limit or fails, it will seamlessly fall back
    to Gemini, Mistral, or NVIDIA depending on API key availability.
    """
    
    fallbacks = _build_fallbacks()
    
    try:
        response = completion(
            model=model,
            messages=messages,
            fallbacks=fallbacks,
            **kwargs
        )
        return response
    except Exception as e:
        print(f"[DEBUG: llm_provider] LLM generation failed across all providers. Error: {e}")
        raise e

def get_instructor_client():
    """
    Returns an instructor client patched with litellm.
    This allows us to use standard Pydantic models with fallbacks natively.
    """
    client = instructor.from_litellm(completion)
    
    # Wrap the create method to inject fallbacks automatically
    original_create = client.chat.completions.create
    
    def create_with_fallbacks(*args, **kwargs):
        # Inject fallbacks into the litellm kwargs if not already provided
        if "fallbacks" not in kwargs:
            kwargs["fallbacks"] = _build_fallbacks()
        # Default model to groq if not provided
        if "model" not in kwargs:
            kwargs["model"] = "groq/llama-3.3-70b-versatile"
            
        return original_create(*args, **kwargs)
        
    client.chat.completions.create = create_with_fallbacks
    return client
