import os
import logging
import litellm
import instructor
from litellm import completion, acompletion
from tenacity import retry, stop_after_attempt, wait_exponential
from core.config import settings
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class LLMProviderError(Exception):
    """Raised when all LLM providers fail to generate a response."""
    pass

# Pre-configure environment variables for litellm based on our settings
os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY
if settings.GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = settings.GEMINI_API_KEY
if settings.MISTRAL_API_KEY:
    os.environ["MISTRAL_API_KEY"] = settings.MISTRAL_API_KEY
if settings.NVIDIA_API_KEY:
    os.environ["NVIDIA_NIM_API_KEY"] = settings.NVIDIA_API_KEY

# Fix: Disable LiteLLM's internal async LoggingWorker to prevent
# 'Task was destroyed but it is pending!' warnings on request teardown.
litellm.suppress_debug_info = True
litellm._async_success_callback = []
litellm.callbacks = []

# CRITICAL: Tell LiteLLM to silently drop kwargs that a specific provider doesn't support.
# Without this, if Groq fails and it falls back to Gemini, Gemini throws a 400 BadRequest
# for unknown args (like certain instructor kwargs), which aborts the fallback chain completely.
litellm.drop_params = True

# Sampling params that Gemini does not accept and will throw deprecation warnings for
_GEMINI_INCOMPATIBLE_PARAMS = {"temperature", "top_p", "top_k", "presence_penalty", "frequency_penalty"}

def _is_valid_key(key: Optional[str]) -> bool:
    if not key or not key.strip():
        return False
    # Exclude common template placeholder strings
    lower_key = key.lower()
    if "your" in lower_key or "sk-" in lower_key and len(key) < 10:
        if "your_api_key" in lower_key or "your-api-key" in lower_key or "..." in lower_key:
            return False
    return True

def _build_fallbacks() -> List[Dict[str, str]]:
    """Builds a dynamic list of fallback models based on available API keys."""
    fallbacks = [
        {"model": "groq/llama-3.3-70b-versatile"}
    ]
    
    # Priority 1: Gemini
    if _is_valid_key(settings.GEMINI_API_KEY):
        fallbacks.append({"model": "gemini/gemini-1.5-flash"})
        
    # Priority 2: Mistral
    if _is_valid_key(settings.MISTRAL_API_KEY):
        fallbacks.append({"model": "mistral/mistral-large-latest"})
        
    # Priority 3: NVIDIA
    if _is_valid_key(settings.NVIDIA_API_KEY):
        # Example nvidia model, replace with your preferred model
        fallbacks.append({
            "model": "nvidia_nim/meta/llama3-70b-instruct",
            "api_base": "https://integrate.api.nvidia.com/v1"
        })
        
    return fallbacks

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_chat_completion(messages: List[Dict[str, str]], model: str = "groq/llama-3.3-70b-versatile", **kwargs) -> Any:
    """
    Unified LLM chat completion with automatic fallback routing.
    If the primary model (Groq) hits a rate limit or fails, it will seamlessly fall back
    to Gemini, Mistral, or NVIDIA depending on API key availability.
    """
    
    fallbacks = _build_fallbacks()
    
    # Only strip Gemini-incompatible params if the PRIMARY model is Gemini.
    # For fallback routing, litellm.drop_params=True (set above) handles provider-specific param stripping.
    if model.startswith("gemini/"):
        kwargs = {k: v for k, v in kwargs.items() if k not in _GEMINI_INCOMPATIBLE_PARAMS}
    
    try:
        api_base = kwargs.get('api_base', 'default')
        logger.debug("Requesting LLM completion | Primary Model: %s | api_base: %s | fallbacks: %s", model, api_base, [f['model'] for f in fallbacks])
        
        import time
        start_time = time.time()
        
        response = completion(
            model=model,
            messages=messages,
            fallbacks=fallbacks,
            **kwargs
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        try:
            from services.metrics_service import emit_provider_event
            
            def get_provider(m: str):
                return m.split("/")[0] if m and "/" in m else str(m)
                
            actual_model = getattr(response, "model", model)
            actual_provider = get_provider(actual_model)
            primary_provider = get_provider(model)
            
            if actual_model != model:
                emit_provider_event(primary_provider, "failure", latency_ms)
                emit_provider_event(actual_provider, "fallback", latency_ms)
                emit_provider_event(actual_provider, "success", latency_ms)
            else:
                emit_provider_event(actual_provider, "success", latency_ms)
        except Exception as e:
            logger.warning(f"Failed to emit provider metrics: {e}")
            
        logger.debug("Successfully used model: %s", getattr(response, 'model', model))
        return response
    except Exception as e:
        logger.error("LLM generation failed across all providers: %s", e, exc_info=True)
        try:
            from services.metrics_service import emit_provider_event
            primary_provider = model.split("/")[0] if "/" in model else model
            emit_provider_event(primary_provider, "failure", 0)
        except Exception:
            pass
        
        raise LLMProviderError(
            f"LLM generation failed across all fallback providers. Last error: {e}"
        )

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def async_generate_chat_completion(messages: List[Dict[str, str]], model: str = "groq/llama-3.3-70b-versatile", **kwargs) -> Any:
    """
    Async version of unified LLM chat completion with automatic fallback routing.
    """
    fallbacks = _build_fallbacks()
    if model.startswith("gemini/"):
        kwargs = {k: v for k, v in kwargs.items() if k not in _GEMINI_INCOMPATIBLE_PARAMS}
    
    try:
        api_base = kwargs.get('api_base', 'default')
        logger.debug("Requesting Async LLM completion | Primary Model: %s | api_base: %s | fallbacks: %s", model, api_base, [f['model'] for f in fallbacks])
        import time
        start_time = time.time()
        
        response = await acompletion(
            model=model,
            messages=messages,
            fallbacks=fallbacks,
            **kwargs
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        try:
            from services.metrics_service import emit_provider_event
            def get_provider(m: str):
                return m.split("/")[0] if m and "/" in m else str(m)
            actual_model = getattr(response, "model", model)
            actual_provider = get_provider(actual_model)
            primary_provider = get_provider(model)
            if actual_model != model:
                emit_provider_event(primary_provider, "failure", latency_ms)
                emit_provider_event(actual_provider, "fallback", latency_ms)
                emit_provider_event(actual_provider, "success", latency_ms)
            else:
                emit_provider_event(actual_provider, "success", latency_ms)
        except Exception as e:
            logger.warning(f"Failed to emit provider metrics: {e}")
            
        return response
    except Exception as e:
        logger.error("Async LLM generation failed: %s", e, exc_info=True)
        try:
            from services.metrics_service import emit_provider_event
            primary_provider = model.split("/")[0] if "/" in model else model
            emit_provider_event(primary_provider, "failure", 0)
        except Exception:
            pass
        raise LLMProviderError(f"LLM generation failed across all fallback providers. Last error: {e}")

_instructor_client = None
_async_instructor_client = None

def get_instructor_client():
    """
    Returns a cached instructor client patched with litellm.
    Uses a module-level singleton to avoid re-creating and monkey-patching on every call.
    """
    global _instructor_client
    if _instructor_client is not None:
        return _instructor_client
        
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
            
        logger.debug("Requesting Structured LLM completion (Primary: %s)", kwargs['model'])
        return original_create(*args, **kwargs)
        
    client.chat.completions.create = create_with_fallbacks
    _instructor_client = client
    return _instructor_client

def get_async_instructor_client():
    """
    Returns a cached async instructor client patched with litellm acompletion.
    Uses a module-level singleton to avoid re-creating and monkey-patching on every call.
    """
    global _async_instructor_client
    if _async_instructor_client is not None:
        return _async_instructor_client
        
    client = instructor.from_litellm(acompletion)
    
    # Wrap the create method to inject fallbacks automatically
    original_create = client.chat.completions.create
    
    async def create_with_fallbacks(*args, **kwargs):
        # Inject fallbacks into the litellm kwargs if not already provided
        if "fallbacks" not in kwargs:
            kwargs["fallbacks"] = _build_fallbacks()
        # Default model to groq if not provided
        if "model" not in kwargs:
            kwargs["model"] = "groq/llama-3.3-70b-versatile"
            
        logger.debug("Requesting Async Structured LLM completion (Primary: %s)", kwargs['model'])
        return await original_create(*args, **kwargs)
        
    client.chat.completions.create = create_with_fallbacks
    _async_instructor_client = client
    return _async_instructor_client
