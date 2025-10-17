"""
Chat history service - orchestrates PostgreSQL and Qdrant operations.

This service provides a unified interface for managing chat sessions and messages,
handling both relational metadata (PostgreSQL) and vector embeddings (Qdrant).
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID
import uuid

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.chat_models import ChatSession, ChatMessage
from app.core.database import db_manager
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class ChatHistoryService:
    """
    Service for managing chat sessions and message history.
    
    Orchestrates operations across PostgreSQL (metadata) and 
    Qdrant (vector embeddings) to provide context-aware chat.
    """
    
    def create_session(
        self,
        user_id: Optional[str] = None
    ) -> ChatSession:
        """
        Create a new chat session.
        
        Args:
            user_id: Optional user identifier
        
        Returns:
            ChatSession object with generated session_id
        
        Raises:
            RuntimeError: If session creation fails
        """
        try:
            with db_manager.session_scope() as db:
                # Create new session
                session = ChatSession(
                    session_id=uuid.uuid4(),
                    user_id=user_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(session)
                db.commit()
                db.refresh(session)
                
                logger.info(f"Created new session: {session.session_id}")
                return session
                
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise RuntimeError(f"Could not create session: {e}")
    
    def get_session(
        self,
        session_id: UUID
    ) -> Optional[ChatSession]:
        """
        Get a session by ID.
        
        Args:
            session_id: Session UUID
        
        Returns:
            ChatSession object or None if not found
        """
        try:
            with db_manager.session_scope() as db:
                session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id
                ).first()
                
                return session
                
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return None
    
    def get_or_create_session(
        self,
        session_id: Optional[UUID] = None,
        user_id: Optional[str] = None
    ) -> ChatSession:
        """
        Get existing session or create a new one.
        
        Args:
            session_id: Optional existing session ID
            user_id: Optional user identifier
        
        Returns:
            ChatSession object
        """
        if session_id:
            session = self.get_session(session_id)
            if session:
                return session
            
            logger.warning(
                f"Session {session_id} not found, creating new session"
            )
        
        return self.create_session(user_id=user_id)
    
    def save_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        generate_embedding: bool = True
    ) -> Tuple[ChatMessage, Optional[str]]:
        """
        Save a message to both PostgreSQL and Qdrant.
        
        Args:
            session_id: Session UUID
            role: 'user' or 'assistant'
            content: Message text content
            generate_embedding: Whether to generate and store embedding
        
        Returns:
            Tuple of (ChatMessage object, Qdrant point_id)
        
        Raises:
            RuntimeError: If message save fails
        """
        try:
            # 1. Save to PostgreSQL first
            with db_manager.session_scope() as db:
                message = ChatMessage(
                    session_id=session_id,
                    role=role,
                    content=content,
                    timestamp=datetime.utcnow(),
                    vector_id=None  # Will update after Qdrant storage
                )
                
                db.add(message)
                db.commit()
                db.refresh(message)
                
                message_id = message.id
            
            logger.debug(
                f"Saved message {message_id} to PostgreSQL "
                f"(session: {session_id})"
            )
            
            # 2. Generate embedding and store in Qdrant
            point_id = None
            
            if generate_embedding:
                try:
                    # Generate embedding
                    embedding = embedding_service.generate_embedding(content)
                    
                    # Store in Qdrant
                    point_id = qdrant_service.store_message(
                        message_id=message_id,
                        session_id=str(session_id),
                        role=role,
                        content=content,
                        embedding=embedding,
                        timestamp=message.timestamp
                    )
                    
                    # Update PostgreSQL with vector_id
                    with db_manager.session_scope() as db:
                        msg = db.query(ChatMessage).filter(
                            ChatMessage.id == message_id
                        ).first()
                        
                        if msg:
                            msg.vector_id = point_id
                            db.commit()
                    
                    logger.debug(
                        f"Stored message {message_id} embedding in Qdrant "
                        f"(point: {point_id})"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Failed to store embedding for message {message_id}: {e}"
                    )
                    # Continue without embedding - message is still saved
            
            # 3. Update session timestamp
            self._update_session_timestamp(session_id)
            
            return message, point_id
            
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
            raise RuntimeError(f"Could not save message: {e}")
    
    def get_relevant_context(
        self,
        session_id: UUID,
        query: str,
        limit: Optional[int] = None,
        exclude_roles: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context for a query using semantic search.
        
        Args:
            session_id: Session UUID
            query: Query text to find similar messages
            limit: Maximum number of context messages (default: from config)
            exclude_roles: Roles to exclude from results
        
        Returns:
            List of relevant messages with similarity scores
        """
        if limit is None:
            limit = settings.retrieval_top_k
        
        try:
            # Generate embedding for query
            query_embedding = embedding_service.generate_embedding(query)
            
            # Search for similar messages in Qdrant
            results = qdrant_service.search_similar_messages(
                query_embedding=query_embedding,
                session_id=str(session_id),
                limit=limit,
                score_threshold=settings.retrieval_score_threshold,
                exclude_roles=exclude_roles
            )
            
            logger.info(
                f"Retrieved {len(results)} relevant context messages "
                f"for session {session_id}"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve context: {e}")
            return []
    
    def get_session_messages(
        self,
        session_id: UUID,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ChatMessage]:
        """
        Get all messages for a session (chronological order).
        
        Args:
            session_id: Session UUID
            limit: Maximum number of messages
            offset: Number of messages to skip
        
        Returns:
            List of ChatMessage objects
        """
        try:
            with db_manager.session_scope() as db:
                query = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).order_by(ChatMessage.timestamp)
                
                if offset:
                    query = query.offset(offset)
                
                if limit:
                    query = query.limit(limit)
                
                messages = query.all()
                
                return messages
                
        except Exception as e:
            logger.error(f"Failed to get session messages: {e}")
            return []
    
    def get_recent_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get recent sessions, optionally filtered by user.
        
        Args:
            user_id: Optional user identifier
            limit: Maximum number of sessions
        
        Returns:
            List of session dictionaries with metadata
        """
        try:
            with db_manager.session_scope() as db:
                query = db.query(ChatSession).order_by(
                    desc(ChatSession.updated_at)
                )
                
                if user_id:
                    query = query.filter(ChatSession.user_id == user_id)
                
                query = query.limit(limit)
                
                sessions = query.all()
                
                # Format sessions with message counts
                result = []
                for session in sessions:
                    message_count = db.query(ChatMessage).filter(
                        ChatMessage.session_id == session.session_id
                    ).count()
                    
                    result.append({
                        "session_id": str(session.session_id),
                        "user_id": session.user_id,
                        "created_at": session.created_at.isoformat(),
                        "updated_at": session.updated_at.isoformat(),
                        "message_count": message_count
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get recent sessions: {e}")
            return []
    
    def delete_session(
        self,
        session_id: UUID
    ) -> bool:
        """
        Delete a session and all its messages from both databases.
        
        Args:
            session_id: Session UUID
        
        Returns:
            True if successful
        """
        try:
            # 1. Delete from Qdrant
            deleted_count = qdrant_service.delete_session_messages(
                str(session_id)
            )
            logger.info(
                f"Deleted {deleted_count} vectors from Qdrant "
                f"for session {session_id}"
            )
            
            # 2. Delete from PostgreSQL (cascades to messages)
            with db_manager.session_scope() as db:
                session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id
                ).first()
                
                if session:
                    db.delete(session)
                    db.commit()
                    logger.info(f"Deleted session {session_id} from PostgreSQL")
                    return True
                else:
                    logger.warning(f"Session {session_id} not found")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    def format_context_for_llm(
        self,
        context_messages: List[Dict[str, Any]],
        max_length: Optional[int] = None
    ) -> str:
        """
        Format retrieved context messages for LLM prompt.
        
        Args:
            context_messages: List of context message dictionaries
            max_length: Maximum character length (default: from config)
        
        Returns:
            Formatted context string
        """
        if not context_messages:
            return ""
        
        if max_length is None:
            max_length = settings.retrieval_max_context_length
        
        # Format each message
        formatted_parts = []
        total_length = 0
        
        for msg in context_messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            score = msg.get('score', 0.0)
            
            # Format: [User] message text (relevance: 0.85)
            formatted = f"[{role.capitalize()}] {content} (relevance: {score:.2f})"
            
            # Check length limit
            if total_length + len(formatted) > max_length:
                break
            
            formatted_parts.append(formatted)
            total_length += len(formatted)
        
        if not formatted_parts:
            return ""
        
        # Combine into context block
        context = "\n".join([
            "Previously discussed (relevant context):",
            "---",
            *formatted_parts,
            "---"
        ])
        
        return context
    
    def _update_session_timestamp(self, session_id: UUID):
        """
        Update session's updated_at timestamp.
        
        Args:
            session_id: Session UUID
        """
        try:
            with db_manager.session_scope() as db:
                session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id
                ).first()
                
                if session:
                    session.updated_at = datetime.utcnow()
                    db.commit()
                    
        except Exception as e:
            logger.error(f"Failed to update session timestamp: {e}")
    
    def get_session_stats(
        self,
        session_id: UUID
    ) -> Dict[str, Any]:
        """
        Get statistics for a session.
        
        Args:
            session_id: Session UUID
        
        Returns:
            Dictionary with session statistics
        """
        try:
            with db_manager.session_scope() as db:
                session = db.query(ChatSession).filter(
                    ChatSession.session_id == session_id
                ).first()
                
                if not session:
                    return {}
                
                # Count messages by role
                user_count = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id,
                    ChatMessage.role == 'user'
                ).count()
                
                assistant_count = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id,
                    ChatMessage.role == 'assistant'
                ).count()
                
                total_count = user_count + assistant_count
                
                # Get first and last message timestamps
                first_message = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).order_by(ChatMessage.timestamp).first()
                
                last_message = db.query(ChatMessage).filter(
                    ChatMessage.session_id == session_id
                ).order_by(desc(ChatMessage.timestamp)).first()
                
                return {
                    "session_id": str(session_id),
                    "created_at": session.created_at.isoformat(),
                    "updated_at": session.updated_at.isoformat(),
                    "total_messages": total_count,
                    "user_messages": user_count,
                    "assistant_messages": assistant_count,
                    "first_message_at": first_message.timestamp.isoformat() if first_message else None,
                    "last_message_at": last_message.timestamp.isoformat() if last_message else None,
                }
                
        except Exception as e:
            logger.error(f"Failed to get session stats: {e}")
            return {}


# Global singleton instance
chat_history_service = ChatHistoryService()


def get_chat_history_service() -> ChatHistoryService:
    """
    Get the global chat history service instance.
    
    Returns:
        ChatHistoryService instance
    """
    return chat_history_service

