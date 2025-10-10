"""
Chat schema definitions for request/response models
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    """Single message in conversation"""
    
    role: str = Field(..., description="Role of the message sender (user or assistant)")
    content: str = Field(..., description="Content of the message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Hello, how are you?"
            }
        }


class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    
    message: str = Field(..., min_length=1, description="User's message")
    history: Optional[List[Message]] = Field(default=None, description="Conversation history")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Hello, how are you?",
                "history": [
                    {"role": "user", "content": "Hi"},
                    {"role": "assistant", "content": "Hello! How can I help you?"}
                ]
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    
    reply: str = Field(..., description="Assistant's reply message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reply": "I'm doing well, thank you for asking! How can I assist you today?"
            }
        }

