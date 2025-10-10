"""
Ollama service - handles all interactions with the Ollama API
"""

import httpx
from typing import List, Dict
from fastapi import HTTPException

from app.core.config import settings


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
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Generate a chat response from Ollama
        
        Args:
            user_message: The user's current message
            conversation_history: Optional list of previous messages
            
        Returns:
            The assistant's response text
            
        Raises:
            HTTPException: If the Ollama request fails
        """
        # Build the complete message array
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history if provided
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

