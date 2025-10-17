"""
Qdrant service for vector database operations.

Handles storage, retrieval, and semantic search of message embeddings.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
)
from qdrant_client.http import models as qdrant_models

from app.core.config import settings
from app.models.qdrant_schema import QdrantChatSchema

logger = logging.getLogger(__name__)


class QdrantService:
    """
    Service for interacting with Qdrant vector database.
    
    Handles collection management, vector storage, and semantic search.
    """
    
    _instance: Optional['QdrantService'] = None
    _client: Optional[QdrantClient] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Singleton pattern - only one instance of the service."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the Qdrant service."""
        if not self._initialized:
            self._initialize_client()
    
    def _initialize_client(self):
        """
        Initialize Qdrant client and ensure collection exists.
        """
        if self._client is not None:
            logger.info("Qdrant client already initialized")
            return
        
        try:
            logger.info(f"Connecting to Qdrant at {settings.qdrant_url}")
            
            # Initialize client
            self._client = QdrantClient(
                url=settings.qdrant_url,
                timeout=10.0
            )
            
            # Ensure collection exists
            self._ensure_collection()
            
            self._initialized = True
            logger.info("✅ Qdrant client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            raise RuntimeError(f"Could not initialize Qdrant service: {e}")
    
    def _ensure_collection(self):
        """
        Create collection if it doesn't exist, or verify it matches our schema.
        """
        collection_name = settings.qdrant_collection
        
        try:
            # Check if collection exists
            collections = self._client.get_collections().collections
            collection_exists = any(
                col.name == collection_name for col in collections
            )
            
            if collection_exists:
                logger.info(f"Collection '{collection_name}' already exists")
                
                # Verify collection configuration
                collection_info = self._client.get_collection(collection_name)
                vector_size = collection_info.config.params.vectors.size
                
                if vector_size != settings.embedding_dim:
                    logger.warning(
                        f"Collection dimension mismatch: "
                        f"expected {settings.embedding_dim}, got {vector_size}"
                    )
            else:
                # Create collection
                logger.info(f"Creating collection '{collection_name}'...")
                
                self._client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=settings.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                
                # Create payload indexes for efficient filtering
                self._create_payload_indexes()
                
                logger.info(f"✅ Collection '{collection_name}' created successfully")
                
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise
    
    def _create_payload_indexes(self):
        """
        Create indexes on payload fields for efficient filtering.
        """
        collection_name = settings.qdrant_collection
        
        try:
            # Index session_id for session-based filtering
            self._client.create_payload_index(
                collection_name=collection_name,
                field_name="session_id",
                field_schema=qdrant_models.PayloadSchemaType.KEYWORD
            )
            
            # Index role for filtering by message sender
            self._client.create_payload_index(
                collection_name=collection_name,
                field_name="role",
                field_schema=qdrant_models.PayloadSchemaType.KEYWORD
            )
            
            # Index timestamp_unix for time-based filtering
            self._client.create_payload_index(
                collection_name=collection_name,
                field_name="timestamp_unix",
                field_schema=qdrant_models.PayloadSchemaType.INTEGER
            )
            
            logger.info("✅ Payload indexes created")
            
        except Exception as e:
            logger.warning(f"Could not create payload indexes: {e}")
    
    def store_message(
        self,
        message_id: int,
        session_id: str,
        role: str,
        content: str,
        embedding: List[float],
        timestamp: Optional[datetime] = None
    ) -> str:
        """
        Store a message with its embedding in Qdrant.
        
        Args:
            message_id: Database ID of the message
            session_id: UUID of the session
            role: 'user' or 'assistant'
            content: Message text content
            embedding: Vector embedding of the message
            timestamp: Message timestamp (default: now)
        
        Returns:
            Point ID (UUID string) assigned to the message
        
        Raises:
            RuntimeError: If storage fails
        """
        if self._client is None:
            raise RuntimeError("Qdrant client not initialized")
        
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Generate unique point ID
        point_id = str(uuid.uuid4())
        
        # Create payload using schema
        payload = QdrantChatSchema.create_point_payload(
            session_id=session_id,
            message_id=message_id,
            role=role,
            content=content,
            timestamp=timestamp
        )
        
        try:
            # Create point
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            
            # Upload to Qdrant
            self._client.upsert(
                collection_name=settings.qdrant_collection,
                points=[point]
            )
            
            logger.debug(
                f"Stored message {message_id} in Qdrant with point ID {point_id}"
            )
            
            return point_id
            
        except Exception as e:
            logger.error(f"Failed to store message in Qdrant: {e}")
            raise RuntimeError(f"Could not store message: {e}")
    
    def search_similar_messages(
        self,
        query_embedding: List[float],
        session_id: Optional[str] = None,
        limit: int = 5,
        score_threshold: Optional[float] = None,
        exclude_roles: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar messages using vector similarity.
        
        Args:
            query_embedding: Vector embedding of the query
            session_id: Filter by session (None = all sessions)
            limit: Maximum number of results
            score_threshold: Minimum similarity score (0-1)
            exclude_roles: Roles to exclude from results
        
        Returns:
            List of dictionaries with message data and scores
        
        Raises:
            RuntimeError: If search fails
        """
        if self._client is None:
            raise RuntimeError("Qdrant client not initialized")
        
        if score_threshold is None:
            score_threshold = settings.retrieval_score_threshold
        
        try:
            # Build filter conditions
            filter_conditions = []
            
            if session_id:
                filter_conditions.append(
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id)
                    )
                )
            
            if exclude_roles:
                for role in exclude_roles:
                    filter_conditions.append(
                        FieldCondition(
                            key="role",
                            match=MatchValue(value=role),
                        )
                    )
            
            # Create filter (if any conditions)
            search_filter = None
            if filter_conditions:
                if exclude_roles:
                    # Use must_not for exclude
                    search_filter = Filter(
                        must=[c for c in filter_conditions if "session_id" in str(c)],
                        must_not=[c for c in filter_conditions if "role" in str(c)]
                    )
                else:
                    search_filter = Filter(must=filter_conditions)
            
            # Perform search
            results = self._client.search(
                collection_name=settings.qdrant_collection,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=True,
                with_vectors=False  # Don't return vectors to save bandwidth
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "point_id": result.id,
                    "score": result.score,
                    "message_id": result.payload.get("message_id"),
                    "session_id": result.payload.get("session_id"),
                    "role": result.payload.get("role"),
                    "content": result.payload.get("content"),
                    "timestamp": result.payload.get("timestamp"),
                })
            
            logger.debug(
                f"Found {len(formatted_results)} similar messages "
                f"(threshold: {score_threshold})"
            )
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to search similar messages: {e}")
            raise RuntimeError(f"Could not search messages: {e}")
    
    def get_session_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all messages for a specific session.
        
        Args:
            session_id: Session UUID
            limit: Maximum number of messages (None = all)
        
        Returns:
            List of message dictionaries
        """
        if self._client is None:
            raise RuntimeError("Qdrant client not initialized")
        
        try:
            # Scroll through all points with this session_id
            results, _ = self._client.scroll(
                collection_name=settings.qdrant_collection,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="session_id",
                            match=MatchValue(value=session_id)
                        )
                    ]
                ),
                limit=limit or 1000,
                with_payload=True,
                with_vectors=False
            )
            
            # Format results
            messages = []
            for result in results:
                messages.append({
                    "point_id": result.id,
                    "message_id": result.payload.get("message_id"),
                    "role": result.payload.get("role"),
                    "content": result.payload.get("content"),
                    "timestamp": result.payload.get("timestamp"),
                })
            
            return messages
            
        except Exception as e:
            logger.error(f"Failed to get session messages: {e}")
            return []
    
    def delete_message(self, point_id: str) -> bool:
        """
        Delete a message from Qdrant.
        
        Args:
            point_id: Point ID to delete
        
        Returns:
            True if successful
        """
        if self._client is None:
            raise RuntimeError("Qdrant client not initialized")
        
        try:
            self._client.delete(
                collection_name=settings.qdrant_collection,
                points_selector=[point_id]
            )
            
            logger.debug(f"Deleted point {point_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete point: {e}")
            return False
    
    def delete_session_messages(self, session_id: str) -> int:
        """
        Delete all messages for a session.
        
        Args:
            session_id: Session UUID
        
        Returns:
            Number of messages deleted
        """
        if self._client is None:
            raise RuntimeError("Qdrant client not initialized")
        
        try:
            # Delete by filter
            result = self._client.delete(
                collection_name=settings.qdrant_collection,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="session_id",
                            match=MatchValue(value=session_id)
                        )
                    ]
                )
            )
            
            logger.info(f"Deleted messages for session {session_id}")
            return result.operation_id if result else 0
            
        except Exception as e:
            logger.error(f"Failed to delete session messages: {e}")
            return 0
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the Qdrant collection.
        
        Returns:
            Dictionary with collection metadata
        """
        if self._client is None:
            raise RuntimeError("Qdrant client not initialized")
        
        try:
            collection_info = self._client.get_collection(
                settings.qdrant_collection
            )
            
            return {
                "collection_name": settings.qdrant_collection,
                "vector_size": collection_info.config.params.vectors.size,
                "distance": collection_info.config.params.vectors.distance.name,
                "points_count": collection_info.points_count,
                "indexed_vectors_count": collection_info.indexed_vectors_count,
                "status": collection_info.status.name,
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return {}
    
    def check_health(self) -> bool:
        """
        Check if Qdrant is healthy and accessible.
        
        Returns:
            True if healthy
        """
        try:
            if self._client is None:
                return False
            
            # Try to get collections list
            collections = self._client.get_collections()
            
            # Check if our collection exists
            collection_exists = any(
                col.name == settings.qdrant_collection
                for col in collections.collections
            )
            
            return collection_exists
            
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False
    
    def is_initialized(self) -> bool:
        """
        Check if service is initialized.
        
        Returns:
            True if initialized
        """
        return self._initialized and self._client is not None


# Global singleton instance
qdrant_service = QdrantService()


def get_qdrant_service() -> QdrantService:
    """
    Get the global Qdrant service instance.
    
    Returns:
        QdrantService singleton instance
    """
    return qdrant_service

