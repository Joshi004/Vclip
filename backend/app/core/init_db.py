"""
Database initialization script.

Run this to set up the database schema and verify connections.
"""

import logging
from app.core.database import init_db, check_db_health
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_database():
    """
    Initialize the PostgreSQL database.
    
    Creates all tables defined in SQLAlchemy models.
    """
    logger.info("=" * 60)
    logger.info("DATABASE INITIALIZATION")
    logger.info("=" * 60)
    
    # Show configuration
    logger.info(f"Database URL: {settings.database_url.split('@')[1]}")  # Hide password
    
    try:
        # Initialize database
        logger.info("Creating database tables...")
        init_db()
        
        # Verify connection
        logger.info("Verifying database connection...")
        if check_db_health():
            logger.info("✅ Database is healthy and ready")
        else:
            logger.error("❌ Database health check failed")
            return False
        
        logger.info("=" * 60)
        logger.info("DATABASE INITIALIZATION COMPLETE")
        logger.info("=" * 60)
        
        # Show created tables
        logger.info("\nTables created:")
        logger.info("  - chat_sessions")
        logger.info("  - chat_messages")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = initialize_database()
    exit(0 if success else 1)

