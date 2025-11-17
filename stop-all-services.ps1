# 2-Aside Application Stop Script
# Stops all running services (uvicorn and node processes)

Write-Host "========================================" -ForegroundColor Red
Write-Host "  Stopping 2-Aside Application Services" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

# Function to kill processes on a specific port
function Stop-ServiceOnPort {
    param(
        [int]$Port,
        [string]$ServiceName
    )

    Write-Host "Stopping $ServiceName on port $Port..." -ForegroundColor Yellow

    try {
        $connections = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"

        if ($connections) {
            $connections | ForEach-Object {
                $line = $_.Line.Trim()
                $processId = $line -split '\s+' | Select-Object -Last 1

                if ($processId -match '^\d+$') {
                    try {
                        Stop-Process -Id $processId -Force -ErrorAction Stop
                        Write-Host "  [OK] Stopped process $processId" -ForegroundColor Green
                    }
                    catch {
                        Write-Host "  [ERROR] Could not stop process $processId" -ForegroundColor Red
                    }
                }
            }
        }
        else {
            Write-Host "  - No service running on port $Port" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "  [ERROR] Error checking port $Port" -ForegroundColor Red
    }
}

# Stop all backend services
Write-Host "Stopping Backend Services..." -ForegroundColor Cyan
Write-Host ""

Stop-ServiceOnPort -Port 8000 -ServiceName "API Gateway"
Stop-ServiceOnPort -Port 8001 -ServiceName "Auth Service"
Stop-ServiceOnPort -Port 8002 -ServiceName "Wallet Service"
Stop-ServiceOnPort -Port 8003 -ServiceName "User Service"
Stop-ServiceOnPort -Port 8004 -ServiceName "Funding Service"

Write-Host ""
Write-Host "Stopping Frontend..." -ForegroundColor Cyan
Stop-ServiceOnPort -Port 3000 -ServiceName "Frontend"

Write-Host ""
Write-Host "Stopping any remaining uvicorn or node processes..." -ForegroundColor Yellow

# Stop any remaining uvicorn processes
try {
    $uvicornProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*uvicorn*"
    }

    if ($uvicornProcesses) {
        $uvicornProcesses | ForEach-Object {
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Stopped uvicorn process $($_.Id)" -ForegroundColor Green
        }
    }
}
catch {
    # Silently continue if no processes found
}

# Stop any remaining node processes (frontend)
try {
    $nodeProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*next dev*" -or $_.CommandLine -like "*npm*"
    }

    if ($nodeProcesses) {
        $nodeProcesses | ForEach-Object {
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  [OK] Stopped node process $($_.Id)" -ForegroundColor Green
        }
    }
}
catch {
    # Silently continue if no processes found
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  All Services Stopped Successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
