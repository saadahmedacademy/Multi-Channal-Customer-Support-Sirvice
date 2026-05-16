#!/bin/bash
# Security scanning script for local development

set -e

echo "========================================="
echo "Security Scanning - AI Customer Support"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Install security tools if not present
echo -e "${YELLOW}Installing security tools...${NC}"
pip install -q pip-audit bandit safety 2>/dev/null || true

echo ""
echo "========================================="
echo "1. Dependency Vulnerability Scan"
echo "========================================="
echo ""

# Scan Python dependencies
echo -e "${YELLOW}Scanning Python dependencies with pip-audit...${NC}"
if pip-audit -r backend/requirements.txt; then
    echo -e "${GREEN}✓ No vulnerabilities found in Python dependencies${NC}"
else
    echo -e "${RED}✗ Vulnerabilities found in Python dependencies${NC}"
fi

echo ""
echo -e "${YELLOW}Scanning Python dependencies with safety...${NC}"
if safety check -r backend/requirements.txt --json > safety-report.json 2>/dev/null; then
    echo -e "${GREEN}✓ Safety check passed${NC}"
else
    echo -e "${YELLOW}⚠ Safety check found issues (see safety-report.json)${NC}"
fi

echo ""
echo "========================================="
echo "2. Static Application Security Testing"
echo "========================================="
echo ""

# Run Bandit
echo -e "${YELLOW}Running Bandit SAST scan...${NC}"
if bandit -r backend/ -f json -o bandit-report.json 2>/dev/null; then
    echo -e "${GREEN}✓ Bandit scan completed${NC}"
else
    echo -e "${YELLOW}⚠ Bandit found potential issues (see bandit-report.json)${NC}"
fi

# Show summary
if [ -f bandit-report.json ]; then
    HIGH_SEVERITY=$(jq '[.results[] | select(.issue_severity=="HIGH")] | length' bandit-report.json 2>/dev/null || echo "0")
    MEDIUM_SEVERITY=$(jq '[.results[] | select(.issue_severity=="MEDIUM")] | length' bandit-report.json 2>/dev/null || echo "0")

    echo "  High severity issues: $HIGH_SEVERITY"
    echo "  Medium severity issues: $MEDIUM_SEVERITY"
fi

echo ""
echo "========================================="
echo "3. Secret Scanning"
echo "========================================="
echo ""

# Check for common secret patterns
echo -e "${YELLOW}Scanning for exposed secrets...${NC}"

SECRET_PATTERNS=(
    "password\s*=\s*['\"][^'\"]{8,}"
    "api[_-]?key\s*=\s*['\"][^'\"]{16,}"
    "secret[_-]?key\s*=\s*['\"][^'\"]{16,}"
    "token\s*=\s*['\"][^'\"]{16,}"
    "sk-[a-zA-Z0-9]{32,}"
)

SECRETS_FOUND=0

for pattern in "${SECRET_PATTERNS[@]}"; do
    if grep -r -E "$pattern" backend/ --exclude-dir=__pycache__ --exclude="*.pyc" 2>/dev/null | grep -v "test" | grep -v ".example"; then
        SECRETS_FOUND=$((SECRETS_FOUND + 1))
    fi
done

if [ $SECRETS_FOUND -eq 0 ]; then
    echo -e "${GREEN}✓ No exposed secrets found${NC}"
else
    echo -e "${RED}✗ Potential secrets found in code${NC}"
fi

echo ""
echo "========================================="
echo "4. Configuration Security"
echo "========================================="
echo ""

# Check .env files
echo -e "${YELLOW}Checking environment files...${NC}"

if [ -f .env ]; then
    echo -e "${YELLOW}⚠ .env file exists (should not be committed)${NC}"

    # Check if .env is in .gitignore
    if grep -q "^\.env$" .gitignore 2>/dev/null; then
        echo -e "${GREEN}✓ .env is in .gitignore${NC}"
    else
        echo -e "${RED}✗ .env is NOT in .gitignore${NC}"
    fi
fi

# Check for committed secrets
echo ""
echo -e "${YELLOW}Checking git history for secrets...${NC}"
if git log --all --full-history --source --find-object=$(git hash-object .env 2>/dev/null) 2>/dev/null | grep -q "commit"; then
    echo -e "${RED}✗ .env file found in git history${NC}"
else
    echo -e "${GREEN}✓ No .env file in git history${NC}"
fi

echo ""
echo "========================================="
echo "5. Dependency Audit (Node.js)"
echo "========================================="
echo ""

if [ -d "frontend" ]; then
    cd frontend
    echo -e "${YELLOW}Scanning Node.js dependencies...${NC}"

    if npm audit --audit-level=moderate; then
        echo -e "${GREEN}✓ No vulnerabilities found in Node.js dependencies${NC}"
    else
        echo -e "${RED}✗ Vulnerabilities found in Node.js dependencies${NC}"
    fi
    cd ..
fi

echo ""
echo "========================================="
echo "Summary"
echo "========================================="
echo ""

echo "Reports generated:"
echo "  - bandit-report.json (SAST results)"
echo "  - safety-report.json (dependency vulnerabilities)"
echo ""

echo -e "${YELLOW}Review the reports and fix any critical issues before deploying.${NC}"
echo ""

# Exit with error if critical issues found
if [ $SECRETS_FOUND -gt 0 ]; then
    echo -e "${RED}❌ Security scan failed: Secrets found in code${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Security scan completed${NC}"
exit 0
