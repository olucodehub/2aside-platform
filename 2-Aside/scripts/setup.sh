#!/bin/bash
# 2-Aside Platform - Linux/macOS Setup Script
# Run this script to set up the development environment on Linux or macOS

set -e  # Exit on error

echo "=============================================="
echo "2-Aside Platform - Development Setup"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}[1/7] Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 11 ]; then
        echo -e "${GREEN}✓ Python version OK: Python $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}✗ Python 3.11+ required. Current: Python $PYTHON_VERSION${NC}"
        echo -e "${YELLOW}Please install Python 3.11 or higher${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    echo -e "${YELLOW}Please install Python 3.11 or higher${NC}"
    exit 1
fi

# Check Docker
echo ""
echo -e "${YELLOW}[2/7] Checking Docker installation...${NC}"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker found: $DOCKER_VERSION${NC}"
else
    echo -e "${RED}✗ Docker not found${NC}"
    echo -e "${YELLOW}Please install Docker from https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose found${NC}"
else
    echo -e "${RED}✗ Docker Compose not found${NC}"
    echo -e "${YELLOW}Please install Docker Compose${NC}"
    exit 1
fi

# Check if .env exists
echo ""
echo -e "${YELLOW}[3/7] Checking environment configuration...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env file already exists${NC}"
else
    echo -e "${YELLOW}! .env file not found, creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${CYAN}⚠ IMPORTANT: Edit .env file with your configuration!${NC}"
fi

# Create Python virtual environment
echo ""
echo -e "${YELLOW}[4/7] Creating Python virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}! Virtual environment already exists, skipping...${NC}"
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment and install dependencies
echo ""
echo -e "${YELLOW}[5/7] Installing Python dependencies...${NC}"
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Initialize Git repository (if not already)
echo ""
echo -e "${YELLOW}[6/7] Checking Git repository...${NC}"
if [ -d ".git" ]; then
    echo -e "${GREEN}✓ Git repository already initialized${NC}"
else
    git init
    echo -e "${GREEN}✓ Git repository initialized${NC}"
fi

# Start Docker containers
echo ""
echo -e "${YELLOW}[7/7] Starting Docker containers...${NC}"
echo -e "${CYAN}This may take a few minutes on first run...${NC}"
docker-compose up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Docker containers started successfully${NC}"
else
    echo -e "${RED}✗ Failed to start Docker containers${NC}"
    echo -e "${YELLOW}Check docker-compose logs for details${NC}"
    exit 1
fi

# Display service URLs
echo ""
echo "=============================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=============================================="
echo ""
echo -e "${YELLOW}Service URLs:${NC}"
echo "  API Gateway:     http://localhost:8000"
echo "  Auth Service:    http://localhost:8001"
echo "  User Service:    http://localhost:8002"
echo "  Wallet Service:  http://localhost:8003"
echo "  Funding Service: http://localhost:8004"
echo "  Betting Service: http://localhost:8005"
echo "  Custom Bets:     http://localhost:8006"
echo "  Admin Service:   http://localhost:8007"
echo "  Redis:           http://localhost:6379"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Edit .env file with your Azure SQL credentials"
echo "  2. Run database migrations: ./scripts/migrate.sh"
echo "  3. View logs: docker-compose logs -f"
echo "  4. Stop services: docker-compose down"
echo ""
echo -e "${CYAN}Documentation: See README.md for detailed information${NC}"
echo ""
