"""
Embedding service for generating vector embeddings from text.

Uses sentence-transformers to create semantic embeddings that can be
used for similarity search in Qdrant.
"""

import logging
from typing import List, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings using sentence-transformers.
    
    Implements singleton pattern to ensure model is loaded only once.
    """
    
    _instance: Optional['EmbeddingService'] = None
    _model: Optional[SentenceTransformer] = None
    _initialized: bool = False
    
    def __new__(cls):
        """Singleton pattern - only one instance of the service."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the embedding service (called on first access)."""
        # Lazy initialization - model loaded on first use
        pass
    
    def _initialize_model(self):
        """
        Load the sentence-transformers model.
        
        This is called once on first initialization. The model is cached
        for subsequent use.
        """
        if self._model is not None:
            logger.info("Embedding model already loaded")
            return
        
        try:
            logger.info(f"Loading embedding model: {settings.embedding_model}")
            logger.info(f"Device: {settings.embedding_device}")
            
            # Load model with specified device
            self._model = SentenceTransformer(
                settings.embedding_model,
                device=settings.embedding_device
            )
            
            # Verify dimensions
            test_embedding = self._model.encode("test", show_progress_bar=False)
            actual_dim = len(test_embedding)
            
            if actual_dim != settings.embedding_dim:
                logger.warning(
                    f"Model dimension mismatch: expected {settings.embedding_dim}, "
                    f"got {actual_dim}. Updating configuration."
                )
            
            self._initialized = True
            logger.info(
                f"✅ Embedding model loaded successfully "
                f"({actual_dim} dimensions)"
            )
            
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise RuntimeError(f"Could not initialize embedding service: {e}")
    
    def generate_embedding(
        self,
        text: str,
        normalize: bool = True
    ) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            normalize: Whether to normalize the embedding vector
        
        Returns:
            List of floats representing the embedding vector
        
        Raises:
            RuntimeError: If model is not initialized
            ValueError: If text is empty
        """
        if self._model is None:
            self._initialize_model()
        
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")
        
        try:
            # Generate embedding
            embedding = self._model.encode(
                text,
                normalize_embeddings=normalize,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            
            # Convert to list for JSON serialization
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise RuntimeError(f"Failed to generate embedding: {e}")
    
    def generate_embeddings_batch(
        self,
        texts: List[str],
        normalize: bool = True,
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing).
        
        Batch processing is more efficient than individual calls.
        
        Args:
            texts: List of input texts to embed
            normalize: Whether to normalize the embedding vectors
            show_progress: Whether to show progress bar
        
        Returns:
            List of embedding vectors (one per input text)
        
        Raises:
            RuntimeError: If model is not initialized
            ValueError: If texts list is empty
        """
        if self._model is None:
            self._initialize_model()
        
        if not texts:
            raise ValueError("Cannot generate embeddings for empty list")
        
        # Filter out empty texts
        valid_texts = [text for text in texts if text and text.strip()]
        
        if not valid_texts:
            raise ValueError("All input texts are empty")
        
        if len(valid_texts) < len(texts):
            logger.warning(
                f"Filtered out {len(texts) - len(valid_texts)} empty texts"
            )
        
        try:
            # Generate embeddings in batch
            embeddings = self._model.encode(
                valid_texts,
                normalize_embeddings=normalize,
                show_progress_bar=show_progress,
                batch_size=settings.embedding_batch_size,
                convert_to_numpy=True
            )
            
            # Convert to list of lists for JSON serialization
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise RuntimeError(f"Failed to generate batch embeddings: {e}")
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            Integer dimension of embedding vectors
        """
        if self._model is None:
            return settings.embedding_dim
        
        # Generate a test embedding to get actual dimension
        test_embedding = self._model.encode("test", show_progress_bar=False)
        return len(test_embedding)
    
    def compute_similarity(
        self,
        embedding1: Union[List[float], np.ndarray],
        embedding2: Union[List[float], np.ndarray]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
        
        Returns:
            Similarity score between 0 and 1 (higher is more similar)
        """
        # Convert to numpy arrays if needed
        emb1 = np.array(embedding1) if isinstance(embedding1, list) else embedding1
        emb2 = np.array(embedding2) if isinstance(embedding2, list) else embedding2
        
        # Compute cosine similarity
        # For normalized vectors: similarity = dot product
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        return float(similarity)
    
    def is_initialized(self) -> bool:
        """
        Check if the embedding model is initialized.
        
        Returns:
            True if model is loaded and ready
        """
        return self._initialized and self._model is not None
    
    def get_model_info(self) -> dict:
        """
        Get information about the loaded model.
        
        Returns:
            Dictionary with model metadata
        """
        return {
            "model_name": settings.embedding_model,
            "dimension": self.get_embedding_dimension(),
            "device": settings.embedding_device,
            "batch_size": settings.embedding_batch_size,
            "initialized": self.is_initialized(),
        }


# Global singleton instance
embedding_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    """
    Get the global embedding service instance.
    
    Returns:
        EmbeddingService singleton instance
    """
    return embedding_service

