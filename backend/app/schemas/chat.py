"""
Chat schema definitions for request/response models
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class Message(BaseModel):
    """Single message in conversation"""
    
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[str] = Field(None, description="Message timestamp (ISO format)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Hello, how are you?",
                "timestamp": "2025-10-13T10:30:00"
            }
        }


class ContextMessage(BaseModel):
    """Context message with relevance score"""
    
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")
    score: float = Field(..., description="Relevance score (0-1)")
    timestamp: Optional[str] = Field(None, description="Message timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "I have a dog named Max",
                "score": 0.87,
                "timestamp": "2025-10-13T10:25:00"
            }
        }


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    
    message: str = Field(..., min_length=1, description="User's message")
    session_id: Optional[str] = Field(
        None,
        description="Session ID (UUID). If not provided, a new session will be created"
    )
    history: Optional[List[Message]] = Field(
        default=None,
        description="Conversation history (deprecated - sessions are now stored server-side)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What's my dog's name?",
                "session_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    
    reply: str = Field(..., description="Assistant's reply message")
    session_id: str = Field(..., description="Session ID (UUID)")
    context_used: Optional[List[ContextMessage]] = Field(
        default=None,
        description="Context messages that were used to generate the response"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "reply": "Your dog's name is Max!",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "context_used": [
                    {
                        "role": "user",
                        "content": "I have a dog named Max",
                        "score": 0.87,
                        "timestamp": "2025-10-13T10:25:00"
                    }
                ]
            }
        }


class SessionCreate(BaseModel):
    """Request model for creating a new session"""
    
    user_id: Optional[str] = Field(
        None,
        description="Optional user identifier"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123"
            }
        }


class SessionResponse(BaseModel):
    """Response model for session information"""
    
    session_id: str = Field(..., description="Session UUID")
    user_id: Optional[str] = Field(None, description="User identifier")
    created_at: str = Field(..., description="Session creation timestamp (ISO format)")
    updated_at: str = Field(..., description="Last update timestamp (ISO format)")
    message_count: Optional[int] = Field(None, description="Number of messages in session")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "user_123",
                "created_at": "2025-10-13T10:00:00",
                "updated_at": "2025-10-13T10:30:00",
                "message_count": 8
            }
        }


class SessionListResponse(BaseModel):
    """Response model for listing sessions"""
    
    sessions: List[SessionResponse] = Field(..., description="List of sessions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sessions": [
                    {
                        "session_id": "550e8400-e29b-41d4-a716-446655440000",
                        "user_id": "user_123",
                        "created_at": "2025-10-13T10:00:00",
                        "updated_at": "2025-10-13T10:30:00",
                        "message_count": 8
                    }
                ]
            }
        }


class MessageResponse(BaseModel):
    """Response model for a single message"""
    
    id: int = Field(..., description="Message ID")
    session_id: str = Field(..., description="Session UUID")
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp (ISO format)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 123,
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "user",
                "content": "Hello, how are you?",
                "timestamp": "2025-10-13T10:30:00"
            }
        }


class SessionMessagesResponse(BaseModel):
    """Response model for session messages"""
    
    session_id: str = Field(..., description="Session UUID")
    messages: List[MessageResponse] = Field(..., description="List of messages")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "messages": [
                    {
                        "id": 123,
                        "session_id": "550e8400-e29b-41d4-a716-446655440000",
                        "role": "user",
                        "content": "Hello!",
                        "timestamp": "2025-10-13T10:30:00"
                    }
                ]
            }
        }


class SessionStatsResponse(BaseModel):
    """Response model for session statistics"""
    
    session_id: str = Field(..., description="Session UUID")
    created_at: str = Field(..., description="Session creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    total_messages: int = Field(..., description="Total number of messages")
    user_messages: int = Field(..., description="Number of user messages")
    assistant_messages: int = Field(..., description="Number of assistant messages")
    first_message_at: Optional[str] = Field(None, description="First message timestamp")
    last_message_at: Optional[str] = Field(None, description="Last message timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-10-13T10:00:00",
                "updated_at": "2025-10-13T10:35:00",
                "total_messages": 10,
                "user_messages": 5,
                "assistant_messages": 5,
                "first_message_at": "2025-10-13T10:01:00",
                "last_message_at": "2025-10-13T10:35:00"
            }
        }

