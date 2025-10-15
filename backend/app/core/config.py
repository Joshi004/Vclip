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
    
    # Debug settings
    debug_sql: bool = os.getenv("DEBUG_SQL", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Ollama configuration
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")
    ollama_timeout: float = 60.0
    
    # PostgreSQL configuration
    postgres_host: str = os.getenv("POSTGRES_HOST", "postgres")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "chatbot")
    postgres_user: str = os.getenv("POSTGRES_USER", "chatbot_user")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "chatbot_password")
    
    @property
    def database_url(self) -> str:
        """
        Construct PostgreSQL database URL from components.
        
        Returns:
            SQLAlchemy-compatible database URL
        """
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )
    
    # Qdrant configuration
    qdrant_host: str = os.getenv("QDRANT_HOST", "qdrant")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_collection: str = os.getenv("QDRANT_COLLECTION", "chat_history")
    qdrant_grpc_port: int = int(os.getenv("QDRANT_GRPC_PORT", "6334"))
    
    @property
    def qdrant_url(self) -> str:
        """
        Construct Qdrant HTTP URL.
        
        Returns:
            Qdrant HTTP endpoint URL
        """
        return f"http://{self.qdrant_host}:{self.qdrant_port}"
    
    # Embedding model configuration
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    embedding_dim: int = int(os.getenv("EMBEDDING_DIM", "384"))
    embedding_device: str = os.getenv("EMBEDDING_DEVICE", "cpu")  # 'cpu' or 'cuda'
    embedding_batch_size: int = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))
    
    # Context retrieval configuration
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "5"))
    retrieval_score_threshold: float = float(os.getenv("RETRIEVAL_SCORE_THRESHOLD", "0.5"))
    retrieval_max_context_length: int = int(os.getenv("RETRIEVAL_MAX_CONTEXT_LENGTH", "2000"))
    
    # Session configuration
    session_timeout_hours: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    max_messages_per_session: int = int(os.getenv("MAX_MESSAGES_PER_SESSION", "1000"))
    
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
    
    def get_config_summary(self) -> dict:
        """
        Get a summary of current configuration (safe for logging).
        
        Returns:
            Dictionary with configuration values (passwords masked)
        """
        return {
            "app_name": self.app_name,
            "app_version": self.app_version,
            "ollama_url": self.ollama_base_url,
            "ollama_model": self.ollama_model,
            "postgres_host": self.postgres_host,
            "postgres_db": self.postgres_db,
            "qdrant_url": self.qdrant_url,
            "qdrant_collection": self.qdrant_collection,
            "embedding_model": self.embedding_model,
            "embedding_dim": self.embedding_dim,
            "retrieval_top_k": self.retrieval_top_k,
            "log_level": self.log_level,
        }


# Global settings instance
settings = Settings()

