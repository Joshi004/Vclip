"""
Configuration module for the chatbot application.
Loads environment variables and provides application settings.
"""

import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application settings
    app_name: str = "Chatbot API"
    app_version: str = "1.0.0"
    
    # Ollama configuration
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")
    ollama_timeout: float = 60.0
    
    # CORS settings
    cors_origins: List[str] = [
        "http://localhost:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:80"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

