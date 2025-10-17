"""
Health check endpoint - checks all service dependencies
"""

from fastapi import APIRouter
import logging

from app.schemas.health import HealthResponse, ServiceHealth
from app.services.ollama_service import ollama_service
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
from app.core.database import check_db_health
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health_check():
    """
    Comprehensive health check for all services.
    
    Checks:
    - PostgreSQL database connection
    - Qdrant vector database
    - Ollama LLM service
    - Embedding model
    
    Returns:
        HealthResponse with status for each service and overall system status
    """
    # Track overall health
    services_healthy = []
    
    # 1. Check PostgreSQL
    postgres_health = _check_postgres()
    services_healthy.append(postgres_health.status == "healthy")
    
    # 2. Check Qdrant
    qdrant_health = _check_qdrant()
    services_healthy.append(qdrant_health.status == "healthy")
    
    # 3. Check Ollama
    ollama_health = _check_ollama()
    services_healthy.append(ollama_health.status == "healthy")
    
    # 4. Check Embedding Model
    embedding_health = _check_embedding_model()
    services_healthy.append(embedding_health.status == "healthy")
    
    # Determine overall status
    if all(services_healthy):
        overall_status = "healthy"
    elif any(services_healthy):
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    logger.info(f"Health check: {overall_status}")
    
    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        postgres=postgres_health,
        qdrant=qdrant_health,
        ollama=ollama_health,
        embedding_model=embedding_health
    )


def _check_postgres() -> ServiceHealth:
    """
    Check PostgreSQL database connection.
    
    Returns:
        ServiceHealth with PostgreSQL status
    """
    try:
        is_healthy = check_db_health()
        
        if is_healthy:
            return ServiceHealth(
                status="healthy",
                message="Connected",
                details={
                    "host": settings.postgres_host,
                    "database": settings.postgres_db
                }
            )
        else:
            return ServiceHealth(
                status="unhealthy",
                message="Connection failed",
                details={
                    "host": settings.postgres_host,
                    "database": settings.postgres_db
                }
            )
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return ServiceHealth(
            status="unhealthy",
            message=f"Error: {str(e)}",
            details={"host": settings.postgres_host}
        )


def _check_qdrant() -> ServiceHealth:
    """
    Check Qdrant vector database.
    
    Returns:
        ServiceHealth with Qdrant status
    """
    try:
        is_healthy = qdrant_service.check_health()
        
        if is_healthy:
            # Get collection info
            collection_info = qdrant_service.get_collection_info()
            
            return ServiceHealth(
                status="healthy",
                message="Collection ready",
                details={
                    "url": settings.qdrant_url,
                    "collection": settings.qdrant_collection,
                    "vectors_count": collection_info.get("points_count", 0)
                }
            )
        else:
            return ServiceHealth(
                status="unhealthy",
                message="Connection failed",
                details={
                    "url": settings.qdrant_url,
                    "collection": settings.qdrant_collection
                }
            )
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return ServiceHealth(
            status="unhealthy",
            message=f"Error: {str(e)}",
            details={"url": settings.qdrant_url}
        )


def _check_ollama() -> ServiceHealth:
    """
    Check Ollama service.
    
    Returns:
        ServiceHealth with Ollama status
    """
    try:
        model_info = ollama_service.get_model_info()
        
        # Try to verify Ollama is actually accessible
        # We don't generate a full response, just check the service
        return ServiceHealth(
            status="healthy",
            message="Service configured",
            details={
                "url": model_info["ollama_url"],
                "model": model_info["model"]
            }
        )
    except Exception as e:
        logger.error(f"Ollama health check failed: {e}")
        return ServiceHealth(
            status="unhealthy",
            message=f"Error: {str(e)}",
            details={"url": settings.ollama_base_url}
        )


def _check_embedding_model() -> ServiceHealth:
    """
    Check embedding model service.
    
    Returns:
        ServiceHealth with embedding model status
    """
    try:
        is_initialized = embedding_service.is_initialized()
        
        if is_initialized:
            model_info = embedding_service.get_model_info()
            
            return ServiceHealth(
                status="healthy",
                message="Model loaded",
                details={
                    "model": model_info["model_name"],
                    "dimension": model_info["dimension"],
                    "device": model_info["device"]
                }
            )
        else:
            return ServiceHealth(
                status="unhealthy",
                message="Model not initialized",
                details={"model": settings.embedding_model}
            )
    except Exception as e:
        logger.error(f"Embedding model health check failed: {e}")
        return ServiceHealth(
            status="unhealthy",
            message=f"Error: {str(e)}",
            details={"model": settings.embedding_model}
        )

