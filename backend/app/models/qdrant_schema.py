"""
Qdrant vector database schema definition.

Defines the structure for storing chat message embeddings in Qdrant.
"""

from typing import Dict, Any
from datetime import datetime


class QdrantChatSchema:
    """
    Schema definition for chat history in Qdrant.
    
    Each point in the Qdrant collection represents a chat message
    with its embedding vector and associated metadata.
    """
    
    # Collection name
    COLLECTION_NAME = "chat_history"
    
    # Vector dimension (matches all-MiniLM-L6-v2 model)
    VECTOR_DIM = 384
    
    # Distance metric for similarity search
    DISTANCE_METRIC = "Cosine"  # Options: Cosine, Euclid, Dot
    
    @staticmethod
    def create_point_payload(
        session_id: str,
        message_id: int,
        role: str,
        content: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """
        Create a payload (metadata) for a Qdrant point.
        
        Args:
            session_id: UUID of the chat session
            message_id: Database ID of the message
            role: Role of the message sender ('user' or 'assistant')
            content: Text content of the message
            timestamp: When the message was created
        
        Returns:
            Dictionary containing the payload data
        """
        return {
            "session_id": str(session_id),
            "message_id": message_id,
            "role": role,
            "content": content,
            "timestamp": timestamp.isoformat(),
            # Additional metadata for filtering
            "timestamp_unix": int(timestamp.timestamp()),
        }
    
    @staticmethod
    def get_collection_config() -> Dict[str, Any]:
        """
        Get the configuration for creating the Qdrant collection.
        
        Returns:
            Dictionary with collection configuration
        """
        return {
            "collection_name": QdrantChatSchema.COLLECTION_NAME,
            "vector_size": QdrantChatSchema.VECTOR_DIM,
            "distance": QdrantChatSchema.DISTANCE_METRIC,
            "on_disk_payload": True,  # Store payload on disk for memory efficiency
        }
    
    @staticmethod
    def get_index_config() -> Dict[str, Any]:
        """
        Get HNSW index configuration for optimal search performance.
        
        Returns:
            Dictionary with index parameters
        """
        return {
            "m": 16,  # Number of edges per node (higher = better quality, more memory)
            "ef_construct": 100,  # Quality of index construction (higher = better index)
            "full_scan_threshold": 10000,  # Use full scan for small collections
        }


# Qdrant payload field descriptions for documentation
PAYLOAD_FIELDS = {
    "session_id": {
        "type": "string",
        "indexed": True,
        "description": "UUID of the chat session this message belongs to"
    },
    "message_id": {
        "type": "integer",
        "indexed": True,
        "description": "PostgreSQL ID of the message"
    },
    "role": {
        "type": "string",
        "indexed": True,
        "description": "Role of message sender: 'user' or 'assistant'"
    },
    "content": {
        "type": "string",
        "indexed": False,
        "description": "Full text content of the message"
    },
    "timestamp": {
        "type": "string",
        "indexed": False,
        "description": "ISO format timestamp of message creation"
    },
    "timestamp_unix": {
        "type": "integer",
        "indexed": True,
        "description": "Unix timestamp for efficient time-based filtering"
    }
}

