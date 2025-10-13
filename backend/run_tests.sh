#!/bin/bash
#
# Simple test runner script for ChatBot integration tests
#

set -e

echo "🧪 Running ChatBot Integration Tests"
echo "===================================="
echo ""

# Check if we're in the backend directory
if [ ! -f "pytest.ini" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "⚠️  pytest not found. Installing dependencies..."
    pip3 install -r requirements.txt
fi

echo "📦 Dependencies ready"
echo ""

# Run tests
echo "🚀 Running tests..."
echo ""

pytest "$@"

echo ""
echo "✅ Tests complete!"

