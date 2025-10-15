"""
Database models for chat sessions and messages.

These models use SQLAlchemy ORM for PostgreSQL storage.
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()


class ChatSession(Base):
    """
    Represents a chat conversation session.
    
    Each session contains multiple messages and maintains context
    across a conversation.
    """
    __tablename__ = "chat_sessions"
    
    # Primary key - UUID for distributed systems
    session_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )
    
    # User identifier (for future multi-user support)
    user_id = Column(String(255), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationship to messages
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.timestamp"
    )
    
    def __repr__(self):
        return f"<ChatSession(session_id={self.session_id}, created_at={self.created_at})>"


class ChatMessage(Base):
    """
    Represents a single message in a chat conversation.
    
    Messages are stored in PostgreSQL with metadata, while their
    embeddings are stored in Qdrant for semantic search.
    """
    __tablename__ = "chat_messages"
    
    # Primary key - auto-incrementing integer
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to session
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Message metadata
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Reference to Qdrant vector storage
    # This is the point ID in Qdrant collection
    vector_id = Column(String(255), nullable=True, index=True)
    
    # Relationship to session
    session = relationship("ChatSession", back_populates="messages")
    
    def __repr__(self):
        return f"<ChatMessage(id={self.id}, session_id={self.session_id}, role={self.role})>"
    
    def to_dict(self):
        """Convert message to dictionary format"""
        return {
            "id": self.id,
            "session_id": str(self.session_id),
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "vector_id": self.vector_id
        }

