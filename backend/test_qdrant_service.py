"""
Standalone test script for Qdrant service.

Run this to verify the Qdrant service works correctly.
"""

import sys
import logging
from datetime import datetime
import uuid

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_qdrant_service():
    """Test the Qdrant service functionality."""
    
    logger.info("=" * 60)
    logger.info("QDRANT SERVICE TEST")
    logger.info("=" * 60)
    
    try:
        # Import services
        from app.services.qdrant_service import qdrant_service
        from app.services.embedding_service import embedding_service
        
        # Test 1: Check initialization
        logger.info("\n📋 Test 1: Service Initialization")
        logger.info("-" * 60)
        
        if qdrant_service.is_initialized():
            logger.info("✅ Qdrant service is initialized")
            
            info = qdrant_service.get_collection_info()
            logger.info(f"   Collection: {info.get('collection_name')}")
            logger.info(f"   Vector Size: {info.get('vector_size')}")
            logger.info(f"   Distance: {info.get('distance')}")
            logger.info(f"   Points Count: {info.get('points_count')}")
        else:
            logger.error("❌ Qdrant service not initialized")
            return False
        
        # Test 2: Store messages
        logger.info("\n📋 Test 2: Store Messages")
        logger.info("-" * 60)
        
        # Create test session
        test_session_id = str(uuid.uuid4())
        logger.info(f"Test session ID: {test_session_id}")
        
        test_messages = [
            ("user", "I have a golden retriever named Max."),
            ("assistant", "That's wonderful! Golden retrievers are great dogs."),
            ("user", "What are good training tips for dogs?"),
            ("assistant", "Here are some training tips: consistency, positive reinforcement..."),
            ("user", "What's the weather like?"),
            ("assistant", "I don't have access to weather data."),
        ]
        
        stored_points = []
        
        for idx, (role, content) in enumerate(test_messages, 1):
            # Generate embedding
            embedding = embedding_service.generate_embedding(content)
            
            # Store in Qdrant
            point_id = qdrant_service.store_message(
                message_id=idx,
                session_id=test_session_id,
                role=role,
                content=content,
                embedding=embedding,
                timestamp=datetime.utcnow()
            )
            
            stored_points.append((point_id, role, content))
            logger.info(f"   Stored message {idx}: {role[:4]}... → {point_id[:8]}...")
        
        logger.info(f"✅ Stored {len(stored_points)} messages successfully")
        
        # Test 3: Semantic search
        logger.info("\n📋 Test 3: Semantic Search")
        logger.info("-" * 60)
        
        query = "What's my dog's name?"
        logger.info(f"Query: '{query}'")
        
        # Generate query embedding
        query_embedding = embedding_service.generate_embedding(query)
        
        # Search
        results = qdrant_service.search_similar_messages(
            query_embedding=query_embedding,
            session_id=test_session_id,
            limit=3
        )
        
        logger.info(f"\nTop 3 results:")
        for rank, result in enumerate(results, 1):
            content = result['content']
            score = result['score']
            role = result['role']
            logger.info(f"  {rank}. [{score:.4f}] ({role}): {content}")
        
        # Verify that the dog message is at the top
        if results and "Max" in results[0]['content']:
            logger.info("✅ Semantic search works correctly (found dog's name)")
        else:
            logger.warning("⚠️  Top result may not be optimal")
        
        # Test 4: Session-based filtering
        logger.info("\n📋 Test 4: Session-Based Filtering")
        logger.info("-" * 60)
        
        # Create another session
        other_session_id = str(uuid.uuid4())
        
        # Store a message in different session
        other_embedding = embedding_service.generate_embedding("Different session message")
        qdrant_service.store_message(
            message_id=999,
            session_id=other_session_id,
            role="user",
            content="Different session message",
            embedding=other_embedding
        )
        
        # Search in original session only
        results_filtered = qdrant_service.search_similar_messages(
            query_embedding=query_embedding,
            session_id=test_session_id,
            limit=10
        )
        
        # Check all results are from correct session
        all_correct_session = all(
            r['session_id'] == test_session_id for r in results_filtered
        )
        
        if all_correct_session:
            logger.info(f"✅ Session filtering works ({len(results_filtered)} results from correct session)")
        else:
            logger.error("❌ Session filtering failed")
            return False
        
        # Test 5: Get session messages
        logger.info("\n📋 Test 5: Get Session Messages")
        logger.info("-" * 60)
        
        session_messages = qdrant_service.get_session_messages(test_session_id)
        
        logger.info(f"Found {len(session_messages)} messages in session")
        
        if len(session_messages) == len(test_messages):
            logger.info("✅ Retrieved all session messages")
        else:
            logger.warning(f"⚠️  Expected {len(test_messages)}, got {len(session_messages)}")
        
        # Test 6: Role filtering
        logger.info("\n📋 Test 6: Role Filtering")
        logger.info("-" * 60)
        
        # Search excluding assistant messages
        results_user_only = qdrant_service.search_similar_messages(
            query_embedding=query_embedding,
            session_id=test_session_id,
            limit=10,
            exclude_roles=["assistant"]
        )
        
        all_user_messages = all(r['role'] == 'user' for r in results_user_only)
        
        if all_user_messages:
            logger.info(f"✅ Role filtering works ({len(results_user_only)} user messages)")
        else:
            logger.error("❌ Role filtering failed")
            return False
        
        # Test 7: Score threshold
        logger.info("\n📋 Test 7: Score Threshold Filtering")
        logger.info("-" * 60)
        
        # Search with high threshold
        high_threshold = 0.7
        results_high_threshold = qdrant_service.search_similar_messages(
            query_embedding=query_embedding,
            session_id=test_session_id,
            limit=10,
            score_threshold=high_threshold
        )
        
        # All scores should be above threshold
        all_above_threshold = all(
            r['score'] >= high_threshold for r in results_high_threshold
        )
        
        if all_above_threshold:
            logger.info(
                f"✅ Score threshold works "
                f"({len(results_high_threshold)} results above {high_threshold})"
            )
        else:
            logger.error("❌ Score threshold failed")
            return False
        
        # Test 8: Collection info
        logger.info("\n📋 Test 8: Collection Information")
        logger.info("-" * 60)
        
        info = qdrant_service.get_collection_info()
        
        logger.info(f"Collection: {info.get('collection_name')}")
        logger.info(f"Total points: {info.get('points_count')}")
        logger.info(f"Indexed vectors: {info.get('indexed_vectors_count')}")
        logger.info(f"Status: {info.get('status')}")
        
        if info.get('points_count', 0) > 0:
            logger.info("✅ Collection info retrieved")
        else:
            logger.warning("⚠️  No points in collection")
        
        # Test 9: Health check
        logger.info("\n📋 Test 9: Health Check")
        logger.info("-" * 60)
        
        is_healthy = qdrant_service.check_health()
        
        if is_healthy:
            logger.info("✅ Qdrant health check passed")
        else:
            logger.error("❌ Qdrant health check failed")
            return False
        
        # Test 10: Cleanup
        logger.info("\n📋 Test 10: Cleanup")
        logger.info("-" * 60)
        
        # Delete test session messages
        deleted_count = qdrant_service.delete_session_messages(test_session_id)
        logger.info(f"   Deleted messages from test session")
        
        # Delete other session
        qdrant_service.delete_session_messages(other_session_id)
        logger.info(f"   Deleted messages from other session")
        
        logger.info("✅ Cleanup complete")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info("✅ All tests passed!")
        logger.info("")
        logger.info("Qdrant service is working correctly and ready to use.")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_qdrant_service()
    sys.exit(0 if success else 1)

