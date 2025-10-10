"""
Chat endpoint - handles chat requests and responses
"""

from fastapi import APIRouter

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ollama_service import ollama_service

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest):
    """
    Chat endpoint - sends message to Ollama and returns response
    
    Args:
        request: ChatRequest containing the user's message and optional conversation history
        
    Returns:
        ChatResponse with the assistant's reply
        
    Raises:
        HTTPException: If Ollama request fails
    """
    # Convert history to the format expected by the service
    history = None
    if request.history:
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]
    
    # Generate response from Ollama
    reply = await ollama_service.generate_chat_response(
        user_message=request.message,
        conversation_history=history
    )
    
    return ChatResponse(reply=reply)

