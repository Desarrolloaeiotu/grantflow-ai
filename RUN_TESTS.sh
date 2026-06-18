#!/bin/bash
# Quick test runner for Grants.gov retry logic

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   Grants.gov Retry Logic — Test Suite Runner                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if in backend directory
if [ ! -f "pyproject.toml" ] && [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: Not in backend directory${NC}"
    echo "Run from: ./backend"
    exit 1
fi

# 1. Setup virtual environment
echo -e "${YELLOW}1. Setting up Python environment...${NC}"
if [ ! -d "venv" ]; then
    python -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate venv
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo

# 2. Install dependencies
echo -e "${YELLOW}2. Installing dependencies...${NC}"
pip install -q pytest pytest-asyncio pytest-cov httpx structlog pydantic sqlalchemy 2>/dev/null || pip install pytest pytest-asyncio pytest-cov httpx structlog pydantic sqlalchemy
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo

# 3. Run automated tests
echo -e "${YELLOW}3. Running automated tests (pytest)...${NC}"
echo "────────────────────────────────────────────────────────────────"
pytest tests/test_grantsgov_retry.py -v --tb=short
TEST_RESULT=$?
echo "────────────────────────────────────────────────────────────────"
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ All automated tests passed${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
echo

# 4. Run manual tests (optional)
echo -e "${YELLOW}4. Running manual tests (scenarios)...${NC}"
echo "────────────────────────────────────────────────────────────────"
python test_retry_manual.py
MANUAL_RESULT=$?
echo "────────────────────────────────────────────────────────────────"
if [ $MANUAL_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ All manual tests passed${NC}"
else
    echo -e "${RED}✗ Some manual tests failed${NC}"
    exit 1
fi
echo

# 5. Coverage report (optional)
echo -e "${YELLOW}5. Generating coverage report...${NC}"
pytest tests/test_grantsgov_retry.py --cov=app.scrapers.grantsgov_scrapling --cov-report=html -q 2>/dev/null || true
if [ -f "htmlcov/index.html" ]; then
    echo -e "${GREEN}✓ Coverage report generated: htmlcov/index.html${NC}"
fi
echo

# 6. Summary
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                      TEST SUMMARY                              ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo -e "║ ${GREEN}✓ Automated tests${NC}        : PASSED                              ║"
echo -e "║ ${GREEN}✓ Manual scenarios${NC}       : PASSED                              ║"
echo -e "║ ${GREEN}✓ Coverage report${NC}        : GENERATED                           ║"
echo "╠════════════════════════════════════════════════════════════════╣"
echo "║ Next steps:                                                    ║"
echo "║ 1. Review code: git diff HEAD~1 backend/app/scrapers/...     ║"
echo "║ 2. Commit: git commit -m 'feat(scraper): retry logic'        ║"
echo "║ 3. Push: git push origin main                                 ║"
echo "║ 4. Monitor: Check Grants.gov success rate for 24 hours       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo

exit 0
