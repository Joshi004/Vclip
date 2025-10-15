"""
Configuration validation script.

Run this to verify all configuration settings and test connections
to external services (PostgreSQL, Qdrant, Ollama).
"""

import sys
import logging
from typing import Dict, Tuple

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def validate_config() -> Dict[str, Tuple[bool, str]]:
    """
    Validate all configuration settings and test service connections.
    
    Returns:
        Dictionary with validation results for each component
    """
    results = {}
    
    # ========================================
    # 1. Load Configuration
    # ========================================
    logger.info("=" * 60)
    logger.info("CONFIGURATION VALIDATION")
    logger.info("=" * 60)
    
    try:
        from app.core.config import settings
        results["config_load"] = (True, "Configuration loaded successfully")
        logger.info("✅ Configuration loaded")
    except Exception as e:
        results["config_load"] = (False, f"Failed to load configuration: {e}")
        logger.error(f"❌ Configuration load failed: {e}")
        return results
    
    # ========================================
    # 2. Display Configuration
    # ========================================
    logger.info("\n" + "-" * 60)
    logger.info("Configuration Summary:")
    logger.info("-" * 60)
    
    config_summary = settings.get_config_summary()
    for key, value in config_summary.items():
        logger.info(f"  {key:25s}: {value}")
    
    # ========================================
    # 3. Validate PostgreSQL Configuration
    # ========================================
    logger.info("\n" + "-" * 60)
    logger.info("PostgreSQL Configuration:")
    logger.info("-" * 60)
    logger.info(f"  Host: {settings.postgres_host}")
    logger.info(f"  Port: {settings.postgres_port}")
    logger.info(f"  Database: {settings.postgres_db}")
    logger.info(f"  User: {settings.postgres_user}")
    logger.info(f"  URL: {settings.database_url.split('@')[1]}")  # Hide password
    
    try:
        from app.core.database import check_db_health
        
        if check_db_health():
            results["postgresql"] = (True, "PostgreSQL connection successful")
            logger.info("✅ PostgreSQL connection successful")
        else:
            results["postgresql"] = (False, "PostgreSQL connection failed")
            logger.error("❌ PostgreSQL connection failed")
    except Exception as e:
        results["postgresql"] = (False, f"PostgreSQL error: {e}")
        logger.error(f"❌ PostgreSQL error: {e}")
    
    # ========================================
    # 4. Validate Qdrant Configuration
    # ========================================
    logger.info("\n" + "-" * 60)
    logger.info("Qdrant Configuration:")
    logger.info("-" * 60)
    logger.info(f"  Host: {settings.qdrant_host}")
    logger.info(f"  Port: {settings.qdrant_port}")
    logger.info(f"  Collection: {settings.qdrant_collection}")
    logger.info(f"  URL: {settings.qdrant_url}")
    
    try:
        import httpx
        
        response = httpx.get(f"{settings.qdrant_url}/healthz", timeout=5.0)
        if response.status_code == 200:
            results["qdrant"] = (True, "Qdrant connection successful")
            logger.info("✅ Qdrant connection successful")
        else:
            results["qdrant"] = (False, f"Qdrant returned status {response.status_code}")
            logger.error(f"❌ Qdrant returned status {response.status_code}")
    except Exception as e:
        results["qdrant"] = (False, f"Qdrant error: {e}")
        logger.error(f"❌ Qdrant error: {e}")
    
    # ========================================
    # 5. Validate Embedding Configuration
    # ========================================
    logger.info("\n" + "-" * 60)
    logger.info("Embedding Configuration:")
    logger.info("-" * 60)
    logger.info(f"  Model: {settings.embedding_model}")
    logger.info(f"  Dimensions: {settings.embedding_dim}")
    logger.info(f"  Device: {settings.embedding_device}")
    logger.info(f"  Batch Size: {settings.embedding_batch_size}")
    
    try:
        logger.info("  Testing model load (this may take a moment)...")
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer(settings.embedding_model, device=settings.embedding_device)
        
        # Test embedding generation
        test_text = "This is a test sentence."
        embedding = model.encode(test_text)
        
        if len(embedding) == settings.embedding_dim:
            results["embedding"] = (True, f"Embedding model loaded ({len(embedding)} dims)")
            logger.info(f"✅ Embedding model loaded successfully")
            logger.info(f"   Generated {len(embedding)}-dimensional embedding")
        else:
            results["embedding"] = (False, f"Dimension mismatch: got {len(embedding)}, expected {settings.embedding_dim}")
            logger.error(f"❌ Dimension mismatch: got {len(embedding)}, expected {settings.embedding_dim}")
    except Exception as e:
        results["embedding"] = (False, f"Embedding model error: {e}")
        logger.error(f"❌ Embedding model error: {e}")
    
    # ========================================
    # 6. Validate Retrieval Configuration
    # ========================================
    logger.info("\n" + "-" * 60)
    logger.info("Retrieval Configuration:")
    logger.info("-" * 60)
    logger.info(f"  Top K: {settings.retrieval_top_k}")
    logger.info(f"  Score Threshold: {settings.retrieval_score_threshold}")
    logger.info(f"  Max Context Length: {settings.retrieval_max_context_length}")
    
    if 0.0 <= settings.retrieval_score_threshold <= 1.0:
        results["retrieval"] = (True, "Retrieval configuration valid")
        logger.info("✅ Retrieval configuration valid")
    else:
        results["retrieval"] = (False, "Score threshold must be between 0.0 and 1.0")
        logger.error("❌ Score threshold must be between 0.0 and 1.0")
    
    # ========================================
    # 7. Validate Ollama Configuration (Optional)
    # ========================================
    logger.info("\n" + "-" * 60)
    logger.info("Ollama Configuration:")
    logger.info("-" * 60)
    logger.info(f"  URL: {settings.ollama_base_url}")
    logger.info(f"  Model: {settings.ollama_model}")
    logger.info(f"  Timeout: {settings.ollama_timeout}s")
    
    try:
        import httpx
        
        response = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=5.0)
        if response.status_code == 200:
            results["ollama"] = (True, "Ollama connection successful")
            logger.info("✅ Ollama connection successful")
        else:
            results["ollama"] = (False, f"Ollama returned status {response.status_code}")
            logger.warning(f"⚠️  Ollama returned status {response.status_code}")
    except Exception as e:
        results["ollama"] = (False, f"Ollama error: {e}")
        logger.warning(f"⚠️  Ollama error: {e} (This is optional)")
    
    # ========================================
    # 8. Summary
    # ========================================
    logger.info("\n" + "=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for success, _ in results.values() if success)
    total = len(results)
    
    for component, (success, message) in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {component:20s}: {message}")
    
    logger.info("=" * 60)
    logger.info(f"Results: {passed}/{total} checks passed")
    logger.info("=" * 60)
    
    return results


def main():
    """Main entry point for validation script."""
    try:
        results = validate_config()
        
        # Exit with error code if any validation failed
        all_passed = all(success for success, _ in results.values())
        sys.exit(0 if all_passed else 1)
        
    except KeyboardInterrupt:
        logger.info("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nFatal error during validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

