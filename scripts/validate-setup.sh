#!/bin/bash
# Quickstart Validation Script
# Validates that all services are running and configured correctly

set -e

echo "========================================="
echo "AI Customer Support Agent - Setup Validator"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL++))
}

check_warn() {
    echo -e "${YELLOW}!${NC} $1"
    ((WARN++))
}

# Check Python
echo "Checking Python..."
if command -v python &> /dev/null || command -v python3 &> /dev/null; then
    PYTHON_CMD=$(command -v python &> /dev/null && echo "python" || echo "python3")
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    check_pass "Python found: $PYTHON_VERSION"
else
    check_fail "Python not found"
fi

# Check Node.js
echo ""
echo "Checking Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    check_pass "Node.js found: $NODE_VERSION"
else
    check_warn "Node.js not found (required for frontend)"
fi

# Check Docker
echo ""
echo "Checking Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    check_pass "Docker found: $DOCKER_VERSION"
    
    if docker ps &> /dev/null; then
        check_pass "Docker daemon is running"
    else
        check_fail "Docker daemon is not running"
    fi
else
    check_warn "Docker not found (required for Redpanda)"
fi

# Check Redpanda container
echo ""
echo "Checking Redpanda..."
if docker ps | grep -q redpanda; then
    check_pass "Redpanda container is running"
else
    check_warn "Redpanda container is not running"
    echo "  Start with: docker-compose -f docker-compose.redpanda.yml up -d"
fi

# Check virtual environment
echo ""
echo "Checking Python virtual environment..."
if [ -d ".venv" ]; then
    check_pass "Virtual environment exists"
    
    if [ -f ".venv/bin/activate" ]; then
        check_pass "Virtual environment is activatable"
    else
        check_fail "Virtual environment activation script missing"
    fi
else
    check_fail "Virtual environment not found"
    echo "  Create with: python -m venv .venv"
fi

# Check requirements
echo ""
echo "Checking Python dependencies..."
if [ -f "backend/requirements.txt" ]; then
    check_pass "requirements.txt exists"
else
    check_fail "requirements.txt not found"
fi

# Check .env file
echo ""
echo "Checking environment configuration..."
if [ -f ".env" ]; then
    check_pass ".env file exists"
    
    # Check required variables
    if grep -q "DATABASE_URL=" .env; then
        check_pass "DATABASE_URL is configured"
    else
        check_fail "DATABASE_URL not configured in .env"
    fi
    
    if grep -q "OPENROUTER_API_KEY=" .env || grep -q "GEMINI_API_KEY=" .env; then
        check_pass "AI API key is configured"
    else
        check_warn "No AI API key configured (OPENROUTER_API_KEY or GEMINI_API_KEY)"
    fi
    
    if grep -q "KAFKA_BOOTSTRAP_SERVERS=" .env; then
        check_pass "KAFKA_BOOTSTRAP_SERVERS is configured"
    else
        check_warn "KAFKA_BOOTSTRAP_SERVERS not configured"
    fi
else
    check_warn ".env file not found (copy from .env.example)"
    echo "  Create with: cp .env.example .env"
fi

# Check .env.example
echo ""
echo "Checking .env.example..."
if [ -f ".env.example" ]; then
    check_pass ".env.example exists"
else
    check_fail ".env.example not found"
fi

# Check backend structure
echo ""
echo "Checking backend structure..."
if [ -d "backend/api" ]; then
    check_pass "backend/api directory exists"
else
    check_fail "backend/api directory not found"
fi

if [ -d "backend/worker" ]; then
    check_pass "backend/worker directory exists"
else
    check_fail "backend/worker directory not found"
fi

if [ -d "backend/integrations" ]; then
    check_pass "backend/integrations directory exists"
else
    check_fail "backend/integrations directory not found"
fi

# Check frontend structure
echo ""
echo "Checking frontend structure..."
if [ -d "frontend" ]; then
    check_pass "frontend directory exists"
else
    check_fail "frontend directory not found"
fi

if [ -f "frontend/package.json" ]; then
    check_pass "frontend/package.json exists"
else
    check_fail "frontend/package.json not found"
fi

# Check database
echo ""
echo "Checking database..."
if [ -f "database/schema.sql" ]; then
    check_pass "database/schema.sql exists"
else
    check_fail "database/schema.sql not found"
fi

if [ -f "database/seed.sql" ]; then
    check_pass "database/seed.sql exists"
else
    check_warn "database/seed.sql not found"
fi

# Check context files
echo ""
echo "Checking knowledge base..."
if [ -f "context/knowledge_base.json" ]; then
    check_pass "knowledge_base.json exists"
else
    check_fail "knowledge_base.json not found"
fi

if [ -f "context/escalation_rules.json" ]; then
    check_pass "escalation_rules.json exists"
else
    check_warn "escalation_rules.json not found"
fi

# Summary
echo ""
echo "========================================="
echo "Validation Summary"
echo "========================================="
echo -e "${GREEN}Passed:${NC} $PASS"
echo -e "${RED}Failed:${NC} $FAIL"
echo -e "${YELLOW}Warnings:${NC} $WARN"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}All critical checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Start Redpanda: docker-compose -f docker-compose.redpanda.yml up -d"
    echo "  2. Activate venv: source .venv/bin/activate"
    echo "  3. Install deps: pip install -r backend/requirements.txt"
    echo "  4. Start backend: cd backend && uvicorn api.main:app --reload"
    echo "  5. Start worker: python backend/worker/message_processor.py"
    echo "  6. Start frontend: cd frontend && npm run dev"
    exit 0
else
    echo -e "${RED}Some critical checks failed. Please fix the issues above.${NC}"
    exit 1
fi
