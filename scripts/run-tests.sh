#!/bin/bash
# Test Runner Script
# Runs all tests with coverage and generates reports

set -e

echo "========================================="
echo "AI Customer Support Agent - Test Suite"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo "Creating virtual environment..."
    python -m venv .venv
    source .venv/bin/activate
fi

# Install test dependencies
echo ""
echo -e "${BLUE}Installing test dependencies...${NC}"
pip install -q pytest pytest-asyncio pytest-cov httpx fastapi 2>/dev/null
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Run tests
echo ""
echo -e "${BLUE}Running test suite...${NC}"
echo "========================================="

# Create test results directory
mkdir -p test-results

# Run unit tests
echo ""
echo -e "${YELLOW}Running Unit Tests...${NC}"
python -m pytest tests/unit/ \
    -v \
    --tb=short \
    --cov=backend/worker \
    --cov-report=term-missing \
    -m unit \
    --junitxml=test-results/unit-results.xml \
    2>&1 | tee test-results/unit-output.txt

UNIT_EXIT=$?

# Run API tests
echo ""
echo -e "${YELLOW}Running API Tests...${NC}"
python -m pytest tests/api/ \
    -v \
    --tb=short \
    --cov=backend/api \
    --cov-report=term-missing \
    -m api \
    --junitxml=test-results/api-results.xml \
    2>&1 | tee test-results/api-output.txt

API_EXIT=$?

# Run integration tests
echo ""
echo -e "${YELLOW}Running Integration Tests...${NC}"
python -m pytest tests/integration/ \
    -v \
    --tb=short \
    --cov=backend \
    --cov-report=term-missing \
    -m "integration or e2e" \
    --junitxml=test-results/integration-results.xml \
    2>&1 | tee test-results/integration-output.txt

INTEGRATION_EXIT=$?

# Summary
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="

if [ $UNIT_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ Unit Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Unit Tests: FAILED${NC}"
fi

if [ $API_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ API Tests: PASSED${NC}"
else
    echo -e "${RED}✗ API Tests: FAILED${NC}"
fi

if [ $INTEGRATION_EXIT -eq 0 ]; then
    echo -e "${GREEN}✓ Integration Tests: PASSED${NC}"
else
    echo -e "${RED}✗ Integration Tests: FAILED${NC}"
fi

echo ""
echo "Coverage reports generated in:"
echo "  - htmlcov/ (HTML report)"
echo "  - coverage.xml (XML report)"
echo ""
echo "Test results saved to:"
echo "  - test-results/"

# Generate coverage summary
if [ -f "coverage.xml" ]; then
    echo ""
    echo "========================================="
    echo "Coverage Summary"
    echo "========================================="
    python -m coverage report --skip-covered
fi

# Exit with error if any tests failed
if [ $UNIT_EXIT -ne 0 ] || [ $API_EXIT -ne 0 ] || [ $INTEGRATION_EXIT -ne 0 ]; then
    echo ""
    echo -e "${RED}Some tests failed. Check test-results/ for details.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}All tests passed!${NC}"
exit 0
