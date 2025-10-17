#!/bin/bash
#
# Comprehensive API testing script
#

set -e

API_BASE="http://localhost:8088"
SESSION_ID=""

echo "========================================"
echo "ChatBot API - Comprehensive Test Suite"
echo "========================================"
echo ""

# Test 1: Health Check
echo "=== Test 1: Health Check ==="
HEALTH=$(curl -s "${API_BASE}/health")
echo "$HEALTH" | python3 -m json.tool
echo ""

# Test 2: Create Session
echo "=== Test 2: Create Session ==="
SESSION_RESPONSE=$(curl -s -X POST "${API_BASE}/sessions" -H "Content-Type: application/json")
echo "$SESSION_RESPONSE" | python3 -m json.tool
SESSION_ID=$(echo "$SESSION_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")
echo "Session ID: $SESSION_ID"
echo ""

# Test 3: Send First Message
echo "=== Test 3: Send First Message (introducing context) ==="
CHAT_RESPONSE1=$(curl -s -X POST "${API_BASE}/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Hi! My name is Alice and I have a golden retriever named Max.\", \"session_id\": \"$SESSION_ID\"}")
echo "$CHAT_RESPONSE1" | python3 -m json.tool
echo ""

# Test 4: Send Second Message
echo "=== Test 4: Send Second Message (testing context) ==="
CHAT_RESPONSE2=$(curl -s -X POST "${API_BASE}/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What's my name?\", \"session_id\": \"$SESSION_ID\"}")
echo "$CHAT_RESPONSE2" | python3 -m json.tool
echo ""

# Test 5: Send Third Message
echo "=== Test 5: Send Third Message (testing pet context) ==="
CHAT_RESPONSE3=$(curl -s -X POST "${API_BASE}/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Tell me about my pet\", \"session_id\": \"$SESSION_ID\"}")
echo "$CHAT_RESPONSE3" | python3 -m json.tool
echo ""

# Test 6: Get Session Messages
echo "=== Test 6: Get Session Messages ==="
curl -s "${API_BASE}/sessions/${SESSION_ID}/messages" | python3 -m json.tool
echo ""

# Test 7: Get Session Stats
echo "=== Test 7: Get Session Stats ==="
curl -s "${API_BASE}/sessions/${SESSION_ID}/stats" | python3 -m json.tool
echo ""

# Test 8: List Sessions
echo "=== Test 8: List All Sessions ==="
curl -s "${API_BASE}/sessions" | python3 -m json.tool
echo ""

# Test 9: Test without session_id (should create new session)
echo "=== Test 9: Message without session_id (creates new session) ==="
CHAT_RESPONSE4=$(curl -s -X POST "${API_BASE}/chat" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Hello, this is a test.\"}")
echo "$CHAT_RESPONSE4" | python3 -m json.tool
NEW_SESSION=$(echo "$CHAT_RESPONSE4" | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])")
echo "New Session ID: $NEW_SESSION"
echo ""

# Test 10: Delete Session
echo "=== Test 10: Delete Test Sessions ==="
curl -s -X DELETE "${API_BASE}/sessions/${SESSION_ID}"
echo "✓ Deleted session $SESSION_ID"
curl -s -X DELETE "${API_BASE}/sessions/${NEW_SESSION}"
echo "✓ Deleted session $NEW_SESSION"
echo ""

echo "========================================"
echo "All tests completed successfully!"
echo "========================================"

