"""
Ollama service - handles all interactions with the Ollama API
"""

import httpx
from typing import List, Dict, Optional
from fastapi import HTTPException
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Service class for Ollama API interactions"""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout
        self.system_prompt = "You are a helpful assistant."
    
    async def generate_chat_response(
        self, 
        user_message: str, 
        conversation_history: List[Dict[str, str]] = None,
        context: Optional[str] = None
    ) -> str:
        """
        Generate a chat response from Ollama with optional context.
        
        Args:
            user_message: The user's current message
            conversation_history: Optional list of previous messages (deprecated)
            context: Optional context string with relevant past information
            
        Returns:
            The assistant's response text
            
        Raises:
            HTTPException: If the Ollama request fails
        """
        # Build enhanced system prompt with context if available
        system_content = self.system_prompt
        
        if context:
            system_content = self._build_context_aware_prompt(context)
            logger.debug("Using context-aware system prompt")
        
        # Build the complete message array
        messages = [{"role": "system", "content": system_content}]
        
        # Add conversation history if provided (deprecated - for backward compatibility)
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add the current user message
        messages.append({"role": "user", "content": user_message})
        
        # Prepare the payload for Ollama API
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract the assistant's reply from Ollama response
                assistant_message = data.get("message", {})
                content = assistant_message.get("content", "")
                
                if not content:
                    raise HTTPException(
                        status_code=502,
                        detail="Ollama returned empty response"
                    )
                
                return content
                
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Ollama request timed out. Please try again."
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Ollama API error: {e.response.status_code}"
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to Ollama: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )
    
    def _build_context_aware_prompt(self, context: str) -> str:
        """
        Build an enhanced system prompt that includes relevant context.
        
        Args:
            context: Formatted context string with relevant information
        
        Returns:
            Enhanced system prompt with context
        """
        prompt = f"""{self.system_prompt}

{context}

When answering, use the context above if it's relevant to the user's question. 
Reference specific information from the context naturally in your responses.
If the context doesn't contain relevant information, answer based on your general knowledge."""
        
        return prompt
    
    def get_model_info(self) -> Dict[str, str]:
        """
        Get current Ollama configuration
        
        Returns:
            Dictionary with Ollama URL and model name
        """
        return {
            "ollama_url": self.base_url,
            "model": self.model
        }


# Singleton instance
ollama_service = OllamaService()

