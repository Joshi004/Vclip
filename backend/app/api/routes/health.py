"""
Health check endpoint
"""

from fastapi import APIRouter

from app.schemas.health import HealthResponse
from app.services.ollama_service import ollama_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health_check():
    """
    Health check endpoint
    
    Returns the status of the API and Ollama configuration
    """
    model_info = ollama_service.get_model_info()
    
    return HealthResponse(
        status="ok",
        ollama_url=model_info["ollama_url"],
        model=model_info["model"]
    )

