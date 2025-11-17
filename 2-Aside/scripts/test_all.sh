#!/bin/bash
# 2-Aside Platform - Test Runner Script
# Run all tests across all microservices with coverage

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "=============================================="
echo "2-Aside Platform - Running All Tests"
echo "=============================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo -e "${YELLOW}Please run setup.sh first${NC}"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install pytest pytest-cov pytest-asyncio httpx

# Define services to test
SERVICES=(
    "auth-service"
    "user-service"
    "wallet-service"
    "funding-service"
    "betting-service"
    "custom-bets-service"
    "admin-service"
)

# Track overall success
TOTAL_TESTS=0
FAILED_TESTS=0

# Run tests for each service
for SERVICE in "${SERVICES[@]}"; do
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}Testing: $SERVICE${NC}"
    echo -e "${CYAN}========================================${NC}"

    if [ -d "$SERVICE" ]; then
        # Run pytest with coverage
        if pytest "$SERVICE/tests" --cov="$SERVICE" --cov-report=term-missing -v; then
            echo -e "${GREEN}✓ $SERVICE tests passed${NC}"
        else
            echo -e "${RED}✗ $SERVICE tests failed${NC}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
        fi
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
    else
        echo -e "${YELLOW}! $SERVICE not found, skipping...${NC}"
    fi
done

# Run shared library tests
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Testing: Shared Library${NC}"
echo -e "${CYAN}========================================${NC}"

if [ -d "shared/tests" ]; then
    if pytest shared/tests --cov=shared --cov-report=term-missing -v; then
        echo -e "${GREEN}✓ Shared library tests passed${NC}"
    else
        echo -e "${RED}✗ Shared library tests failed${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
else
    echo -e "${YELLOW}! Shared library tests not found, skipping...${NC}"
fi

# Generate combined coverage report
echo ""
echo -e "${YELLOW}Generating combined coverage report...${NC}"
pytest --cov=. --cov-report=html --cov-report=term-missing

# Display summary
echo ""
echo "=============================================="
if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}All Tests Passed! ✓${NC}"
else
    echo -e "${RED}$FAILED_TESTS/$TOTAL_TESTS Test Suites Failed ✗${NC}"
fi
echo "=============================================="
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${CYAN}Coverage report generated: htmlcov/index.html${NC}"
    echo -e "${YELLOW}Open in browser:${NC} file://$(pwd)/htmlcov/index.html"
    echo ""
    exit 0
else
    echo -e "${RED}Please fix failing tests before proceeding${NC}"
    echo ""
    exit 1
fi
