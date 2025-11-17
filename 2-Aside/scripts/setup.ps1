# 2-Aside Platform - Windows Setup Script (PowerShell)
# Run this script to set up the development environment on Windows

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "2-Aside Platform - Development Setup (Windows)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/7] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python 3\.(1[1-9]|[2-9][0-9])") {
    Write-Host "✓ Python version OK: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Python 3.11+ required. Current: $pythonVersion" -ForegroundColor Red
    Write-Host "Please install Python 3.11 or higher from https://www.python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

# Check Docker
Write-Host ""
Write-Host "[2/7] Checking Docker installation..." -ForegroundColor Yellow
$dockerVersion = docker --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
} else {
    Write-Host "✗ Docker not found" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if .env exists
Write-Host ""
Write-Host "[3/7] Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
} else {
    Write-Host "! .env file not found, creating from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env file created" -ForegroundColor Green
    Write-Host "⚠ IMPORTANT: Edit .env file with your configuration!" -ForegroundColor Magenta
}

# Create Python virtual environment
Write-Host ""
Write-Host "[4/7] Creating Python virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "! Virtual environment already exists, skipping..." -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment and install dependencies
Write-Host ""
Write-Host "[5/7] Installing Python dependencies..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt
Write-Host "✓ Dependencies installed" -ForegroundColor Green

# Initialize Git repository (if not already)
Write-Host ""
Write-Host "[6/7] Checking Git repository..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "✓ Git repository already initialized" -ForegroundColor Green
} else {
    git init
    Write-Host "✓ Git repository initialized" -ForegroundColor Green
}

# Start Docker containers
Write-Host ""
Write-Host "[7/7] Starting Docker containers..." -ForegroundColor Yellow
Write-Host "This may take a few minutes on first run..." -ForegroundColor Cyan
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker containers started successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to start Docker containers" -ForegroundColor Red
    Write-Host "Check docker-compose logs for details" -ForegroundColor Yellow
}

# Display service URLs
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service URLs:" -ForegroundColor Yellow
Write-Host "  API Gateway:     http://localhost:8000" -ForegroundColor White
Write-Host "  Auth Service:    http://localhost:8001" -ForegroundColor White
Write-Host "  User Service:    http://localhost:8002" -ForegroundColor White
Write-Host "  Wallet Service:  http://localhost:8003" -ForegroundColor White
Write-Host "  Funding Service: http://localhost:8004" -ForegroundColor White
Write-Host "  Betting Service: http://localhost:8005" -ForegroundColor White
Write-Host "  Custom Bets:     http://localhost:8006" -ForegroundColor White
Write-Host "  Admin Service:   http://localhost:8007" -ForegroundColor White
Write-Host "  Redis:           http://localhost:6379" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Edit .env file with your Azure SQL credentials" -ForegroundColor White
Write-Host "  2. Run database migrations: .\scripts\migrate.ps1" -ForegroundColor White
Write-Host "  3. View logs: docker-compose logs -f" -ForegroundColor White
Write-Host "  4. Stop services: docker-compose down" -ForegroundColor White
Write-Host ""
Write-Host "Documentation: See README.md for detailed information" -ForegroundColor Cyan
Write-Host ""
