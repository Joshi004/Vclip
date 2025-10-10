"""
Health check schema definitions
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response model for health check endpoint"""
    
    status: str
    ollama_url: str
    model: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ok",
                "ollama_url": "http://host.docker.internal:11434",
                "model": "llama3"
            }
        }

