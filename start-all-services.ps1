# 2-Aside Application Startup Script
# Starts all backend services and frontend in separate PowerShell windows

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting 2-Aside Application Services" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to start a service in a new window
function Start-Service {
    param(
        [string]$ServiceName,
        [string]$Path,
        [string]$Command,
        [int]$Port
    )

    Write-Host "Starting $ServiceName on port $Port..." -ForegroundColor Green
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '=== $ServiceName (Port $Port) ===' -ForegroundColor Yellow; cd '$Path'; $Command"
    Start-Sleep -Seconds 2
}

# Start Backend Services
Write-Host "Starting Backend Services..." -ForegroundColor Cyan
Write-Host ""

Start-Service -ServiceName "API Gateway" -Path "C:\Dev\Rendezvous\2-Aside\api-gateway" -Command "uvicorn main:app --reload --port 8000" -Port 8000
Start-Service -ServiceName "Auth Service" -Path "C:\Dev\Rendezvous\2-Aside\auth-service" -Command "uvicorn main:app --reload --port 8001" -Port 8001
Start-Service -ServiceName "Wallet Service" -Path "C:\Dev\Rendezvous\2-Aside\wallet-service" -Command "uvicorn main:app --reload --port 8002" -Port 8002
Start-Service -ServiceName "User Service" -Path "C:\Dev\Rendezvous\2-Aside\user-service" -Command "uvicorn main:app --reload --port 8003" -Port 8003
Start-Service -ServiceName "Funding Service (with Auto-Matching)" -Path "C:\Dev\Rendezvous\2-Aside\funding-service" -Command "uvicorn main:app --reload --port 8004" -Port 8004

Write-Host ""
Write-Host "Waiting for backend services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Start Frontend
Write-Host ""
Write-Host "Starting Frontend..." -ForegroundColor Cyan
Write-Host "Starting Frontend on port 3000..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Write-Host '=== Frontend (Port 3000) ===' -ForegroundColor Yellow; cd 'C:\Dev\Rendezvous\2aside-frontend'; npm run dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  All Services Started Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend Services:" -ForegroundColor Cyan
Write-Host "  - API Gateway:      http://localhost:8000" -ForegroundColor White
Write-Host "  - Auth Service:     http://localhost:8001" -ForegroundColor White
Write-Host "  - Wallet Service:   http://localhost:8002" -ForegroundColor White
Write-Host "  - User Service:     http://localhost:8003" -ForegroundColor White
Write-Host "  - Funding Service:  http://localhost:8004" -ForegroundColor White
Write-Host ""
Write-Host "Frontend:" -ForegroundColor Cyan
Write-Host "  - Web Application:  http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "API Documentation:" -ForegroundColor Cyan
Write-Host "  - API Gateway:      http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Auth Service:     http://localhost:8001/docs" -ForegroundColor White
Write-Host "  - Wallet Service:   http://localhost:8002/docs" -ForegroundColor White
Write-Host "  - User Service:     http://localhost:8003/docs" -ForegroundColor White
Write-Host "  - Funding Service:  http://localhost:8004/docs" -ForegroundColor White
Write-Host ""
Write-Host "NOTE: Celery, Redis, and Celery Beat are NO LONGER NEEDED!" -ForegroundColor Yellow
Write-Host "      Auto-matching runs inside the Funding Service at 9am, 3pm, 9pm WAT" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this window..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
