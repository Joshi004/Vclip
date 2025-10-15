"""
Database connection and session management.

Handles PostgreSQL connections via SQLAlchemy and Qdrant initialization.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging

from app.core.config import settings
from app.models.chat_models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages PostgreSQL database connections and initialization.
    """
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self):
        """
        Initialize the database engine and create tables.
        """
        if self._initialized:
            logger.info("Database already initialized")
            return
        
        try:
            # Create database engine
            self.engine = create_engine(
                settings.database_url,
                pool_pre_ping=True,  # Verify connections before using
                pool_size=5,
                max_overflow=10,
                echo=settings.debug_sql  # Log SQL queries if debug enabled
            )
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create all tables
            Base.metadata.create_all(bind=self.engine)
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            SQLAlchemy Session instance
        """
        if not self._initialized:
            self.initialize()
        
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope for database operations.
        
        Usage:
            with db_manager.session_scope() as session:
                session.query(ChatSession).all()
        
        Yields:
            SQLAlchemy Session instance
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self):
        """
        Close database connections and cleanup.
        """
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database sessions.
    
    Usage in routes:
        @router.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    
    Yields:
        SQLAlchemy Session instance
    """
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


def init_db():
    """
    Initialize the database - create tables if they don't exist.
    
    This should be called on application startup.
    """
    try:
        db_manager.initialize()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def check_db_health() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        True if database is accessible, False otherwise
    """
    try:
        with db_manager.session_scope() as session:
            # Simple query to check connection
            session.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

