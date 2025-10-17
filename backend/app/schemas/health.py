"""
Health check schema definitions
"""

from pydantic import BaseModel
from typing import Dict, Optional


class ServiceHealth(BaseModel):
    """Health status for a single service"""
    
    status: str  # 'healthy', 'unhealthy', 'degraded'
    message: Optional[str] = None
    details: Optional[Dict] = None


class HealthResponse(BaseModel):
    """
    Comprehensive health check response.
    
    Includes status for all services: PostgreSQL, Qdrant, Ollama, and Embedding model.
    """
    
    status: str  # 'healthy', 'degraded', 'unhealthy'
    version: str
    
    # Service-specific health
    postgres: ServiceHealth
    qdrant: ServiceHealth
    ollama: ServiceHealth
    embedding_model: ServiceHealth
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "postgres": {
                    "status": "healthy",
                    "message": "Connected",
                    "details": {
                        "host": "postgres",
                        "database": "chatbot"
                    }
                },
                "qdrant": {
                    "status": "healthy",
                    "message": "Collection ready",
                    "details": {
                        "collection": "chat_history",
                        "vectors_count": 1234
                    }
                },
                "ollama": {
                    "status": "healthy",
                    "message": "Model available",
                    "details": {
                        "model": "llama3",
                        "url": "http://host.docker.internal:11434"
                    }
                },
                "embedding_model": {
                    "status": "healthy",
                    "message": "Model loaded",
                    "details": {
                        "model": "all-MiniLM-L6-v2",
                        "dimension": 384
                    }
                }
            }
        }

