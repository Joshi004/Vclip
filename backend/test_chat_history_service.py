"""
Standalone test script for chat history service.

Run this to verify the chat history service works correctly.
Requires PostgreSQL, Qdrant, and embedding service to be running.
"""

import sys
import logging
import uuid

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_chat_history_service():
    """Test the chat history service functionality."""
    
    logger.info("=" * 60)
    logger.info("CHAT HISTORY SERVICE TEST")
    logger.info("=" * 60)
    
    try:
        # Import services
        from app.services.chat_history_service import chat_history_service
        from app.core.database import init_db
        
        # Initialize database
        logger.info("\n📋 Initializing Database")
        logger.info("-" * 60)
        init_db()
        logger.info("✅ Database initialized")
        
        # Test 1: Create session
        logger.info("\n📋 Test 1: Create Session")
        logger.info("-" * 60)
        
        session = chat_history_service.create_session(user_id="test_user")
        session_id = session.session_id
        
        logger.info(f"✅ Created session: {session_id}")
        logger.info(f"   User ID: {session.user_id}")
        logger.info(f"   Created at: {session.created_at}")
        
        # Test 2: Save messages
        logger.info("\n📋 Test 2: Save Messages")
        logger.info("-" * 60)
        
        test_messages = [
            ("user", "Hi! My name is Alice and I love Python programming."),
            ("assistant", "Hello Alice! It's great to meet you. Python is an excellent language."),
            ("user", "I also have a golden retriever named Max."),
            ("assistant", "That's wonderful! Golden retrievers are amazing dogs."),
            ("user", "What are some good Python libraries?"),
            ("assistant", "Some popular Python libraries include NumPy, Pandas, and Django."),
        ]
        
        saved_messages = []
        
        for role, content in test_messages:
            message, point_id = chat_history_service.save_message(
                session_id=session_id,
                role=role,
                content=content,
                generate_embedding=True
            )
            
            saved_messages.append(message)
            logger.info(f"   Saved {role:9s} message (ID: {message.id}, Point: {point_id[:8]}...)")
        
        logger.info(f"✅ Saved {len(saved_messages)} messages")
        
        # Test 3: Get session messages
        logger.info("\n📋 Test 3: Get Session Messages")
        logger.info("-" * 60)
        
        messages = chat_history_service.get_session_messages(session_id)
        
        logger.info(f"Retrieved {len(messages)} messages:")
        for msg in messages:
            logger.info(f"   [{msg.role}] {msg.content[:50]}...")
        
        if len(messages) == len(test_messages):
            logger.info("✅ All messages retrieved")
        else:
            logger.error(f"❌ Expected {len(test_messages)}, got {len(messages)}")
            return False
        
        # Test 4: Semantic context retrieval
        logger.info("\n📋 Test 4: Semantic Context Retrieval")
        logger.info("-" * 60)
        
        # Query about name
        query1 = "What's my name?"
        logger.info(f"Query: '{query1}'")
        
        context1 = chat_history_service.get_relevant_context(
            session_id=session_id,
            query=query1,
            limit=3
        )
        
        logger.info(f"Found {len(context1)} relevant messages:")
        for ctx in context1:
            logger.info(f"   [{ctx['score']:.3f}] {ctx['content'][:60]}...")
        
        # Check if "Alice" is in top result
        if context1 and "Alice" in context1[0]['content']:
            logger.info("✅ Correctly found name in context")
        else:
            logger.warning("⚠️  May not have found best context")
        
        # Query about dog
        query2 = "Tell me about my pet"
        logger.info(f"\nQuery: '{query2}'")
        
        context2 = chat_history_service.get_relevant_context(
            session_id=session_id,
            query=query2,
            limit=3
        )
        
        logger.info(f"Found {len(context2)} relevant messages:")
        for ctx in context2:
            logger.info(f"   [{ctx['score']:.3f}] {ctx['content'][:60]}...")
        
        # Check if "Max" or "retriever" is in results
        if context2 and any("Max" in ctx['content'] or "retriever" in ctx['content'] for ctx in context2):
            logger.info("✅ Correctly found pet info in context")
        else:
            logger.warning("⚠️  May not have found best context")
        
        # Test 5: Format context for LLM
        logger.info("\n📋 Test 5: Format Context for LLM")
        logger.info("-" * 60)
        
        formatted = chat_history_service.format_context_for_llm(context1)
        
        logger.info("Formatted context:")
        logger.info(formatted)
        
        if "Previously discussed" in formatted and len(formatted) > 0:
            logger.info("✅ Context formatted correctly")
        else:
            logger.error("❌ Context formatting failed")
            return False
        
        # Test 6: Get or create session
        logger.info("\n📋 Test 6: Get or Create Session")
        logger.info("-" * 60)
        
        # Get existing session
        existing = chat_history_service.get_or_create_session(
            session_id=session_id
        )
        
        if existing.session_id == session_id:
            logger.info("✅ Retrieved existing session")
        else:
            logger.error("❌ Got different session")
            return False
        
        # Create new session (no session_id provided)
        new_session = chat_history_service.get_or_create_session()
        
        if new_session.session_id != session_id:
            logger.info(f"✅ Created new session: {new_session.session_id}")
        else:
            logger.error("❌ Did not create new session")
            return False
        
        # Test 7: Get recent sessions
        logger.info("\n📋 Test 7: Get Recent Sessions")
        logger.info("-" * 60)
        
        recent = chat_history_service.get_recent_sessions(limit=10)
        
        logger.info(f"Found {len(recent)} recent sessions")
        for sess in recent[:3]:  # Show first 3
            logger.info(
                f"   Session {sess['session_id'][:8]}... "
                f"({sess['message_count']} messages)"
            )
        
        if len(recent) >= 2:  # Should have at least our 2 test sessions
            logger.info("✅ Retrieved recent sessions")
        else:
            logger.warning("⚠️  Expected at least 2 sessions")
        
        # Test 8: Get session stats
        logger.info("\n📋 Test 8: Get Session Stats")
        logger.info("-" * 60)
        
        stats = chat_history_service.get_session_stats(session_id)
        
        logger.info(f"Session statistics:")
        logger.info(f"   Total messages: {stats['total_messages']}")
        logger.info(f"   User messages: {stats['user_messages']}")
        logger.info(f"   Assistant messages: {stats['assistant_messages']}")
        logger.info(f"   First message: {stats['first_message_at']}")
        logger.info(f"   Last message: {stats['last_message_at']}")
        
        if stats['total_messages'] == len(test_messages):
            logger.info("✅ Stats are correct")
        else:
            logger.error("❌ Stats mismatch")
            return False
        
        # Test 9: Exclude roles filter
        logger.info("\n📋 Test 9: Exclude Roles Filter")
        logger.info("-" * 60)
        
        # Get context excluding assistant messages
        context_user_only = chat_history_service.get_relevant_context(
            session_id=session_id,
            query="Python programming",
            limit=5,
            exclude_roles=["assistant"]
        )
        
        all_user = all(ctx['role'] == 'user' for ctx in context_user_only)
        
        if all_user:
            logger.info(f"✅ Role filtering works ({len(context_user_only)} user messages)")
        else:
            logger.error("❌ Role filtering failed")
            return False
        
        # Test 10: Cleanup
        logger.info("\n📋 Test 10: Cleanup")
        logger.info("-" * 60)
        
        # Delete test sessions
        deleted1 = chat_history_service.delete_session(session_id)
        deleted2 = chat_history_service.delete_session(new_session.session_id)
        
        if deleted1 and deleted2:
            logger.info("✅ Sessions deleted successfully")
        else:
            logger.warning("⚠️  Some sessions may not have been deleted")
        
        # Verify deletion
        check_session = chat_history_service.get_session(session_id)
        if check_session is None:
            logger.info("✅ Session confirmed deleted")
        else:
            logger.error("❌ Session still exists")
            return False
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info("✅ All tests passed!")
        logger.info("")
        logger.info("Chat history service is working correctly and ready to use.")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_chat_history_service()
    sys.exit(0 if success else 1)

