# Integration Tests

This directory contains integration tests for the ChatBot backend API.

## Test Strategy

These are **controller-level integration tests**, not unit tests. They test the entire flow from HTTP request to response, validating that all components work together correctly.

## What These Tests Validate

### 1. Chat with Context (`test_chat_integration.py`)
- ✅ Creating new chat sessions
- ✅ Storing messages in vector database
- ✅ Retrieving relevant context semantically
- ✅ Context-aware responses
- ✅ Multiple sessions don't interfere
- ✅ Semantic search finds relevant past messages

### 2. Session Management
- ✅ Create, list, get, and delete sessions
- ✅ Retrieve message history for a session

### 3. Performance
- ✅ Response times are acceptable

## Running Tests

### Prerequisites

Make sure all services are running:
```bash
# Start Qdrant, PostgreSQL, and backend
docker compose up -d
```

### Run All Tests

From the `backend` directory:

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_chat_integration.py

# Run specific test class
pytest tests/test_chat_integration.py::TestChatWithContext

# Run specific test
pytest tests/test_chat_integration.py::TestChatWithContext::test_chat_with_context_awareness
```

### Expected Behavior

**Before Implementation:**
- Most tests will fail (expected)
- Tests serve as specification for implementation

**After Implementation:**
- All tests should pass
- Tests validate the complete feature

## Test Data

Tests use simple, predictable data:
- User introduces themselves with specific information
- Follow-up questions test context retrieval
- Multiple topics test semantic search

## Notes

- Tests run against a real backend instance
- Tests assume Ollama is available (or mocked)
- Tests create and clean up their own test data
- Tests are designed to be independent (can run in any order)

