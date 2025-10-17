"""
Session management endpoints - CRUD operations for chat sessions
"""

from fastapi import APIRouter, HTTPException
from uuid import UUID
from typing import Optional
import logging

from app.schemas.chat import (
    SessionCreate,
    SessionResponse,
    SessionListResponse,
    SessionMessagesResponse,
    MessageResponse,
    SessionStatsResponse,
)
from app.services.chat_history_service import chat_history_service

router = APIRouter(prefix="/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)


@router.post("", response_model=SessionResponse, status_code=201)
async def create_session(request: Optional[SessionCreate] = None):
    """
    Create a new chat session.
    
    Args:
        request: Optional SessionCreate with user_id
    
    Returns:
        SessionResponse with created session details
    
    Raises:
        HTTPException: If session creation fails
    """
    try:
        user_id = None
        if request:
            user_id = request.user_id
        
        session = chat_history_service.create_session(user_id=user_id)
        
        logger.info(f"Created new session: {session.session_id}")
        
        return SessionResponse(
            session_id=str(session.session_id),
            user_id=session.user_id,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            message_count=0
        )
        
    except Exception as e:
        logger.error(f"Failed to create session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    user_id: Optional[str] = None,
    limit: int = 20
):
    """
    List recent chat sessions.
    
    Args:
        user_id: Optional filter by user ID
        limit: Maximum number of sessions to return (default: 20)
    
    Returns:
        SessionListResponse with list of sessions
    """
    try:
        sessions_data = chat_history_service.get_recent_sessions(
            user_id=user_id,
            limit=limit
        )
        
        sessions = [
            SessionResponse(
                session_id=s['session_id'],
                user_id=s.get('user_id'),
                created_at=s['created_at'],
                updated_at=s['updated_at'],
                message_count=s.get('message_count', 0)
            )
            for s in sessions_data
        ]
        
        logger.info(f"Retrieved {len(sessions)} sessions")
        
        return SessionListResponse(sessions=sessions)
        
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """
    Get details for a specific session.
    
    Args:
        session_id: Session UUID
    
    Returns:
        SessionResponse with session details
    
    Raises:
        HTTPException: If session not found or invalid UUID
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id format. Must be a valid UUID."
        )
    
    try:
        session = chat_history_service.get_session(session_uuid)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Get message count
        messages = chat_history_service.get_session_messages(session_uuid)
        
        return SessionResponse(
            session_id=str(session.session_id),
            user_id=session.user_id,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
            message_count=len(messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )


@router.get("/{session_id}/messages", response_model=SessionMessagesResponse)
async def get_session_messages(
    session_id: str,
    limit: Optional[int] = None,
    offset: int = 0
):
    """
    Get all messages for a specific session.
    
    Args:
        session_id: Session UUID
        limit: Maximum number of messages to return
        offset: Number of messages to skip
    
    Returns:
        SessionMessagesResponse with list of messages
    
    Raises:
        HTTPException: If session not found or invalid UUID
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id format. Must be a valid UUID."
        )
    
    try:
        # Verify session exists
        session = chat_history_service.get_session(session_uuid)
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        # Get messages
        messages = chat_history_service.get_session_messages(
            session_id=session_uuid,
            limit=limit,
            offset=offset
        )
        
        message_responses = [
            MessageResponse(
                id=msg.id,
                session_id=str(msg.session_id),
                role=msg.role,
                content=msg.content,
                timestamp=msg.timestamp.isoformat()
            )
            for msg in messages
        ]
        
        logger.info(f"Retrieved {len(message_responses)} messages for session {session_id}")
        
        return SessionMessagesResponse(
            session_id=session_id,
            messages=message_responses
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get messages for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get messages: {str(e)}"
        )


@router.get("/{session_id}/stats", response_model=SessionStatsResponse)
async def get_session_stats(session_id: str):
    """
    Get statistics for a specific session.
    
    Args:
        session_id: Session UUID
    
    Returns:
        SessionStatsResponse with session statistics
    
    Raises:
        HTTPException: If session not found or invalid UUID
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id format. Must be a valid UUID."
        )
    
    try:
        stats = chat_history_service.get_session_stats(session_uuid)
        
        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        return SessionStatsResponse(**stats)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stats for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session stats: {str(e)}"
        )


@router.delete("/{session_id}", status_code=204)
async def delete_session(session_id: str):
    """
    Delete a session and all its messages.
    
    This will delete the session from PostgreSQL (which cascades to messages)
    and remove all associated vectors from Qdrant.
    
    Args:
        session_id: Session UUID
    
    Returns:
        204 No Content on success
    
    Raises:
        HTTPException: If session not found or deletion fails
    """
    try:
        session_uuid = UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid session_id format. Must be a valid UUID."
        )
    
    try:
        success = chat_history_service.delete_session(session_uuid)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )
        
        logger.info(f"Deleted session {session_id}")
        return None  # 204 No Content
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )

