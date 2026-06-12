from enum import Enum
from fastapi import HTTPException

class ErrorCode(str, Enum):
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    MEMORY_UNAVAILABLE = "MEMORY_UNAVAILABLE"
    PINECONE_UNAVAILABLE = "PINECONE_UNAVAILABLE"
    TAVILY_UNAVAILABLE = "TAVILY_UNAVAILABLE"
    PROVIDER_FALLBACK = "PROVIDER_FALLBACK"
    HEALTH_DEGRADED = "HEALTH_DEGRADED"

class AtlasError(HTTPException):
    """
    Standardized application exception.
    Ensures errors returned to the client follow a structured JSON format:
    {
        "error": {
            "code": "ERROR_CODE",
            "message": "Human readable message"
        }
    }
    """
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail={"code": code.value, "message": message})
