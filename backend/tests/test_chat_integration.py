"""
Integration tests for chat functionality with context persistence.

These tests validate the entire chat flow:
1. Create a new session
2. Send messages
3. Verify context is stored
4. Verify context is retrieved and used in responses
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestChatWithContext:
    """Integration tests for chat with context storage and retrieval"""
    
    def test_health_check(self):
        """Test that all services are healthy"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        # After implementation, should have these
        assert "qdrant" in data
        assert "postgres" in data
        assert "embedding_model" in data
    
    def test_chat_creates_session_if_not_provided(self):
        """Test that chat endpoint creates a new session if session_id is not provided"""
        response = client.post(
            "/chat",
            json={
                "message": "Hello, my name is John"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return a reply
        assert "reply" in data
        assert len(data["reply"]) > 0
        
        # Should return the session_id that was created
        assert "session_id" in data
        assert data["session_id"] is not None
    
    def test_chat_with_context_awareness(self):
        """
        Test that the bot uses context from previous messages.
        
        Flow:
        1. User introduces themselves
        2. User asks a question requiring context
        3. Bot should use context to provide relevant answer
        """
        # First message: User introduces themselves
        response1 = client.post(
            "/chat",
            json={
                "message": "Hi! My name is Alice and I love Python programming."
            }
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        session_id = data1["session_id"]
        
        # Verify message was stored (context should be used)
        assert "reply" in data1
        
        # Second message: Ask about something mentioned before
        response2 = client.post(
            "/chat",
            json={
                "message": "What programming language did I mention?",
                "session_id": session_id
            }
        )
        
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Bot should reference the context
        assert "reply" in data2
        reply_lower = data2["reply"].lower()
        
        # Bot should mention Python (from context)
        assert "python" in reply_lower
        
        # Should include context information
        assert "context_used" in data2
        assert len(data2["context_used"]) > 0
    
    def test_multiple_sessions_dont_interfere(self):
        """Test that different sessions maintain separate context"""
        
        # Session 1: User likes Python
        response1 = client.post(
            "/chat",
            json={
                "message": "I love Python programming."
            }
        )
        session1_id = response1.json()["session_id"]
        
        # Session 2: User likes JavaScript
        response2 = client.post(
            "/chat",
            json={
                "message": "I love JavaScript programming."
            }
        )
        session2_id = response2.json()["session_id"]
        
        # Verify sessions are different
        assert session1_id != session2_id
        
        # Ask about programming language in session 1
        response3 = client.post(
            "/chat",
            json={
                "message": "What programming language did I mention?",
                "session_id": session1_id
            }
        )
        
        reply1 = response3.json()["reply"].lower()
        assert "python" in reply1
        
        # Ask about programming language in session 2
        response4 = client.post(
            "/chat",
            json={
                "message": "What programming language did I mention?",
                "session_id": session2_id
            }
        )
        
        reply2 = response4.json()["reply"].lower()
        assert "javascript" in reply2
    
    def test_semantic_search_retrieves_relevant_context(self):
        """
        Test that semantic search retrieves relevant past messages,
        not just chronologically recent ones.
        """
        # Create a session with multiple topics
        response1 = client.post(
            "/chat",
            json={"message": "I have a golden retriever named Max."}
        )
        session_id = response1.json()["session_id"]
        
        # Add some unrelated messages
        client.post(
            "/chat",
            json={
                "message": "What's the weather like?",
                "session_id": session_id
            }
        )
        
        client.post(
            "/chat",
            json={
                "message": "Tell me about space exploration.",
                "session_id": session_id
            }
        )
        
        # Ask about the dog (semantically related to first message)
        response_dog = client.post(
            "/chat",
            json={
                "message": "What's my dog's name?",
                "session_id": session_id
            }
        )
        
        data = response_dog.json()
        reply_lower = data["reply"].lower()
        
        # Should remember the dog's name despite intervening messages
        assert "max" in reply_lower
        
        # Context used should include the relevant message
        assert "context_used" in data
        assert len(data["context_used"]) > 0


class TestSessionManagement:
    """Tests for session management endpoints"""
    
    def test_create_new_session(self):
        """Test explicit session creation"""
        response = client.post("/sessions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert "created_at" in data
    
    def test_get_session_messages(self):
        """Test retrieving all messages from a session"""
        # Create session and send messages
        response1 = client.post(
            "/chat",
            json={"message": "First message"}
        )
        session_id = response1.json()["session_id"]
        
        client.post(
            "/chat",
            json={
                "message": "Second message",
                "session_id": session_id
            }
        )
        
        # Get session messages
        response = client.get(f"/sessions/{session_id}/messages")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should have both user messages and assistant responses
        assert "messages" in data
        assert len(data["messages"]) >= 2  # At least 2 user messages
    
    def test_list_sessions(self):
        """Test listing all sessions"""
        # Create a couple of sessions
        client.post("/chat", json={"message": "Test 1"})
        client.post("/chat", json={"message": "Test 2"})
        
        # List sessions
        response = client.get("/sessions")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "sessions" in data
        assert len(data["sessions"]) >= 2
    
    def test_delete_session(self):
        """Test deleting a session"""
        # Create session
        response = client.post("/sessions")
        session_id = response.json()["session_id"]
        
        # Delete session
        delete_response = client.delete(f"/sessions/{session_id}")
        assert delete_response.status_code == 200
        
        # Verify session is deleted (should return 404)
        get_response = client.get(f"/sessions/{session_id}")
        assert get_response.status_code == 404


class TestPerformance:
    """Basic performance validation tests"""
    
    def test_response_time_acceptable(self):
        """Test that response time is reasonable (< 10 seconds for test)"""
        import time
        
        start = time.time()
        response = client.post(
            "/chat",
            json={"message": "Hello"}
        )
        end = time.time()
        
        assert response.status_code == 200
        
        # Should respond within reasonable time (allowing for first load)
        duration = end - start
        assert duration < 10, f"Response took {duration:.2f}s, expected < 10s"

