"""
Standalone test script for embedding service.

Run this to verify the embedding service works correctly.
"""

import sys
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_embedding_service():
    """Test the embedding service functionality."""
    
    logger.info("=" * 60)
    logger.info("EMBEDDING SERVICE TEST")
    logger.info("=" * 60)
    
    try:
        # Import after setting up logging
        from app.services.embedding_service import embedding_service
        
        # Test 1: Check initialization
        logger.info("\n📋 Test 1: Model Initialization")
        logger.info("-" * 60)
        
        if embedding_service.is_initialized():
            logger.info("✅ Model is initialized")
            
            info = embedding_service.get_model_info()
            logger.info(f"   Model: {info['model_name']}")
            logger.info(f"   Dimensions: {info['dimension']}")
            logger.info(f"   Device: {info['device']}")
            logger.info(f"   Batch Size: {info['batch_size']}")
        else:
            logger.error("❌ Model is not initialized")
            return False
        
        # Test 2: Generate single embedding
        logger.info("\n📋 Test 2: Generate Single Embedding")
        logger.info("-" * 60)
        
        test_text = "This is a test sentence for embedding generation."
        logger.info(f"Input text: '{test_text}'")
        
        start_time = time.time()
        embedding = embedding_service.generate_embedding(test_text)
        elapsed = time.time() - start_time
        
        logger.info(f"✅ Generated embedding in {elapsed:.3f}s")
        logger.info(f"   Embedding dimension: {len(embedding)}")
        logger.info(f"   First 5 values: {embedding[:5]}")
        logger.info(f"   Vector norm: {sum(x**2 for x in embedding)**0.5:.4f}")
        
        # Test 3: Generate batch embeddings
        logger.info("\n📋 Test 3: Generate Batch Embeddings")
        logger.info("-" * 60)
        
        test_texts = [
            "I love programming in Python.",
            "Machine learning is fascinating.",
            "What's the weather like today?",
            "How do I make a cake?",
            "Tell me about quantum physics."
        ]
        
        logger.info(f"Generating embeddings for {len(test_texts)} texts...")
        
        start_time = time.time()
        embeddings = embedding_service.generate_embeddings_batch(test_texts)
        elapsed = time.time() - start_time
        
        logger.info(f"✅ Generated {len(embeddings)} embeddings in {elapsed:.3f}s")
        logger.info(f"   Average time per text: {elapsed/len(test_texts):.3f}s")
        
        # Test 4: Compute similarity
        logger.info("\n📋 Test 4: Compute Similarity")
        logger.info("-" * 60)
        
        text1 = "I love programming in Python."
        text2 = "Python is a great programming language."
        text3 = "What's the weather like today?"
        
        emb1 = embedding_service.generate_embedding(text1)
        emb2 = embedding_service.generate_embedding(text2)
        emb3 = embedding_service.generate_embedding(text3)
        
        sim_12 = embedding_service.compute_similarity(emb1, emb2)
        sim_13 = embedding_service.compute_similarity(emb1, emb3)
        
        logger.info(f"Text 1: '{text1}'")
        logger.info(f"Text 2: '{text2}'")
        logger.info(f"Text 3: '{text3}'")
        logger.info(f"")
        logger.info(f"Similarity (1 ↔ 2): {sim_12:.4f} [Related topics]")
        logger.info(f"Similarity (1 ↔ 3): {sim_13:.4f} [Unrelated topics]")
        
        if sim_12 > sim_13:
            logger.info("✅ Similarity works correctly (related > unrelated)")
        else:
            logger.error("❌ Similarity issue (unrelated scored higher)")
            return False
        
        # Test 5: Semantic search simulation
        logger.info("\n📋 Test 5: Semantic Search Simulation")
        logger.info("-" * 60)
        
        query = "How do I learn Python?"
        documents = [
            "Python is a high-level programming language.",
            "I love eating pizza for dinner.",
            "Learning to code requires practice and patience.",
            "The weather forecast says it will rain tomorrow.",
            "Python tutorials are available online for free."
        ]
        
        logger.info(f"Query: '{query}'")
        logger.info(f"Searching through {len(documents)} documents...")
        
        query_emb = embedding_service.generate_embedding(query)
        doc_embs = embedding_service.generate_embeddings_batch(documents)
        
        # Compute similarities
        similarities = [
            (i, doc, embedding_service.compute_similarity(query_emb, doc_emb))
            for i, (doc, doc_emb) in enumerate(zip(documents, doc_embs))
        ]
        
        # Sort by similarity
        similarities.sort(key=lambda x: x[2], reverse=True)
        
        logger.info("\nTop 3 most relevant documents:")
        for rank, (idx, doc, score) in enumerate(similarities[:3], 1):
            logger.info(f"  {rank}. [{score:.4f}] {doc}")
        
        # Verify that Python-related docs are at the top
        top_doc = similarities[0][1]
        if "Python" in top_doc or "code" in top_doc or "tutorials" in top_doc:
            logger.info("✅ Semantic search works correctly")
        else:
            logger.warning("⚠️  Top result may not be optimal")
        
        # Test 6: Error handling
        logger.info("\n📋 Test 6: Error Handling")
        logger.info("-" * 60)
        
        try:
            embedding_service.generate_embedding("")
            logger.error("❌ Should have raised error for empty text")
            return False
        except ValueError:
            logger.info("✅ Correctly handles empty text")
        
        try:
            embedding_service.generate_embeddings_batch([])
            logger.error("❌ Should have raised error for empty list")
            return False
        except ValueError:
            logger.info("✅ Correctly handles empty list")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info("✅ All tests passed!")
        logger.info("")
        logger.info("Embedding service is working correctly and ready to use.")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_embedding_service()
    sys.exit(0 if success else 1)

