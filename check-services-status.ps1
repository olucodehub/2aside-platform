# 2-Aside Application Status Checker
# Checks which services are currently running

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  2-Aside Services Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Function to check if a port is in use
function Test-Port {
    param(
        [int]$Port
    )

    try {
        $connection = netstat -ano | Select-String ":$Port\s" | Select-String "LISTENING"
        return $connection -ne $null
    }
    catch {
        return $false
    }
}

# Function to test HTTP endpoint
function Test-HttpEndpoint {
    param(
        [string]$Url
    )

    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

# Function to display service status
function Show-ServiceStatus {
    param(
        [string]$ServiceName,
        [int]$Port,
        [string]$HealthUrl
    )

    $portInUse = Test-Port -Port $Port
    $isHealthy = $false

    if ($portInUse) {
        $isHealthy = Test-HttpEndpoint -Url $HealthUrl
    }

    Write-Host "$ServiceName (Port $Port): " -NoNewline

    if ($isHealthy) {
        Write-Host "[RUNNING]" -ForegroundColor Green
        Write-Host "  URL: $HealthUrl" -ForegroundColor Gray
    }
    elseif ($portInUse) {
        Write-Host "[PORT IN USE]" -ForegroundColor Yellow
    }
    else {
        Write-Host "[NOT RUNNING]" -ForegroundColor Red
    }

    Write-Host ""
}

# Check Backend Services
Write-Host "Backend Services:" -ForegroundColor Cyan
Write-Host ""

Show-ServiceStatus -ServiceName "API Gateway" -Port 8000 -HealthUrl "http://localhost:8000/health"
Show-ServiceStatus -ServiceName "Auth Service" -Port 8001 -HealthUrl "http://localhost:8001/health"
Show-ServiceStatus -ServiceName "Wallet Service" -Port 8002 -HealthUrl "http://localhost:8002/health"
Show-ServiceStatus -ServiceName "User Service" -Port 8003 -HealthUrl "http://localhost:8003/health"
Show-ServiceStatus -ServiceName "Funding Service" -Port 8004 -HealthUrl "http://localhost:8004/health"

# Check Frontend
Write-Host "Frontend:" -ForegroundColor Cyan
Write-Host ""

$frontendPort = Test-Port -Port 3000
Write-Host "Frontend (Port 3000): " -NoNewline

if ($frontendPort) {
    Write-Host "[RUNNING]" -ForegroundColor Green
    Write-Host "  URL: http://localhost:3000" -ForegroundColor Gray
}
else {
    Write-Host "[NOT RUNNING]" -ForegroundColor Red
}

Write-Host ""

# Check Merge Cycle Scheduler
Write-Host "Special Features:" -ForegroundColor Cyan
Write-Host ""

Write-Host "Auto-Matching Scheduler: " -NoNewline

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8004/merge-cycle/next" -Method GET -TimeoutSec 2 -ErrorAction Stop

    if ($response.data.has_cycle) {
        Write-Host "[ACTIVE]" -ForegroundColor Green
        Write-Host "  Next merge: $($response.data.merge_time_formatted)" -ForegroundColor Gray

        if ($response.data.is_join_window_open) {
            Write-Host "  Join window: OPEN (closes in $($response.data.current_window.seconds_remaining) seconds)" -ForegroundColor Yellow
        }
        else {
            Write-Host "  Join window: Closed (opens at next merge time)" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "[RESPONDING BUT NO CYCLES]" -ForegroundColor Yellow
    }
}
catch {
    if (Test-Port -Port 8004) {
        Write-Host "[FUNDING SERVICE RUNNING]" -ForegroundColor Yellow
    }
    else {
        Write-Host "[NOT AVAILABLE]" -ForegroundColor Red
    }
}

Write-Host ""

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$apiGateway = Test-Port -Port 8000
$authService = Test-Port -Port 8001
$walletService = Test-Port -Port 8002
$userService = Test-Port -Port 8003
$fundingService = Test-Port -Port 8004
$frontend = Test-Port -Port 3000

$runningCount = @($apiGateway, $authService, $walletService, $userService, $fundingService, $frontend | Where-Object { $_ }).Count
$totalCount = 6

Write-Host "Services Running: $runningCount / $totalCount" -ForegroundColor $(if ($runningCount -eq $totalCount) { "Green" } elseif ($runningCount -gt 0) { "Yellow" } else { "Red" })
Write-Host ""

if ($runningCount -eq $totalCount) {
    Write-Host "[OK] All services are running!" -ForegroundColor Green
    Write-Host "  Application ready at: http://localhost:3000" -ForegroundColor Cyan
}
elseif ($runningCount -gt 0) {
    Write-Host "[WARNING] Some services are not running." -ForegroundColor Yellow
    Write-Host "  Run '.\start-all-services.ps1' to start missing services." -ForegroundColor Gray
}
else {
    Write-Host "[ERROR] No services are running." -ForegroundColor Red
    Write-Host "  Run '.\start-all-services.ps1' to start all services." -ForegroundColor Gray
}

Write-Host ""
Write-Host "Quick Actions:" -ForegroundColor Cyan
Write-Host "  Start all:  .\start-all-services.ps1" -ForegroundColor Gray
Write-Host "  Stop all:   .\stop-all-services.ps1" -ForegroundColor Gray
Write-Host "  Check docs: http://localhost:8000/docs" -ForegroundColor Gray
Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
