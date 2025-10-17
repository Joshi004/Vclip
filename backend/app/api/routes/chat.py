"""
Chat endpoint - handles chat requests and responses with context awareness
"""

from fastapi import APIRouter, HTTPException
from uuid import UUID
import logging

from app.schemas.chat import ChatRequest, ChatResponse, ContextMessage
from app.services.ollama_service import ollama_service
from app.services.chat_history_service import chat_history_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(request: ChatRequest):
    """
    Context-aware chat endpoint with persistent history.
    
    This endpoint:
    1. Gets or creates a chat session
    2. Stores the user's message
    3. Retrieves relevant context from past messages
    4. Generates a context-aware response
    5. Stores the assistant's response
    6. Returns the reply with session info and context used
    
    Args:
        request: ChatRequest with message and optional session_id
        
    Returns:
        ChatResponse with reply, session_id, and context used
        
    Raises:
        HTTPException: If any step fails
    """
    try:
        # Step 1: Get or create session
        session_id_uuid = None
        if request.session_id:
            try:
                session_id_uuid = UUID(request.session_id)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid session_id format. Must be a valid UUID."
                )
        
        session = chat_history_service.get_or_create_session(
            session_id=session_id_uuid
        )
        
        logger.info(f"Using session: {session.session_id}")
        
        # Step 2: Store user message
        user_message, _ = chat_history_service.save_message(
            session_id=session.session_id,
            role="user",
            content=request.message,
            generate_embedding=True
        )
        
        logger.info(f"Stored user message (ID: {user_message.id})")
        
        # Step 3: Retrieve relevant context
        context_messages = chat_history_service.get_relevant_context(
            session_id=session.session_id,
            query=request.message,
            limit=5,
            exclude_roles=None  # Include all messages in context
        )
        
        logger.info(f"Retrieved {len(context_messages)} context messages")
        
        # Step 4: Format context for LLM
        context_str = None
        if context_messages:
            context_str = chat_history_service.format_context_for_llm(
                context_messages
            )
        
        # Step 5: Generate response with context
        reply = await ollama_service.generate_chat_response(
            user_message=request.message,
            conversation_history=None,  # We use context instead
            context=context_str
        )
        
        logger.info("Generated response from Ollama")
        
        # Step 6: Store assistant response
        assistant_message, _ = chat_history_service.save_message(
            session_id=session.session_id,
            role="assistant",
            content=reply,
            generate_embedding=True
        )
        
        logger.info(f"Stored assistant message (ID: {assistant_message.id})")
        
        # Step 7: Format context for response
        context_used = None
        if context_messages:
            context_used = [
                ContextMessage(
                    role=ctx['role'],
                    content=ctx['content'],
                    score=ctx['score'],
                    timestamp=ctx.get('timestamp')
                )
                for ctx in context_messages
            ]
        
        # Return response with session info and context
        return ChatResponse(
            reply=reply,
            session_id=str(session.session_id),
            context_used=context_used
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat request: {str(e)}"
        )

