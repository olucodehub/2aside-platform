# ========================================
# 2-Aside Merge Demo Test Script
# ========================================
# This script helps you test the P2P matching system by:
# 1. Showing pending funding and withdrawal requests
# 2. Manually triggering a merge cycle
# 3. Displaying the merge results
#
# ** REMOVE THIS FILE BEFORE PRODUCTION **
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  2-Aside Merge Demo Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if services are running
Write-Host "Checking if services are running..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8004/health" -ErrorAction Stop
    Write-Host "[OK] Funding service is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Funding service is not running on port 8004" -ForegroundColor Red
    Write-Host "Please start services first: .\start-all-services.ps1" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Get auth token
Write-Host "Please provide admin credentials for testing:" -ForegroundColor Yellow
$email = Read-Host "Admin Email"
$password = Read-Host "Admin Password" -AsSecureString
$passwordPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($password))

Write-Host ""
Write-Host "Logging in..." -ForegroundColor Yellow

try {
    $loginBody = @{
        email = $email
        password = $passwordPlain
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8001/login" -Method Post -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.access_token
    Write-Host "[OK] Login successful" -ForegroundColor Green
    Write-Host "[DEBUG] User: $($loginResponse.user.username) (Admin: $($loginResponse.user.is_admin))" -ForegroundColor Gray
} catch {
    Write-Host "[ERROR] Login failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 1: Viewing Pending Requests" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

try {
    $headers = @{
        Authorization = "Bearer $token"
    }

    $pendingResponse = Invoke-RestMethod -Uri "http://localhost:8004/demo/pending-requests" -Headers $headers -Method Get

    $fundingData = $pendingResponse.data.funding_requests
    $withdrawalData = $pendingResponse.data.withdrawal_requests

    Write-Host ""
    Write-Host "Funding Requests:" -ForegroundColor Yellow
    Write-Host "  Count: $($fundingData.count)" -ForegroundColor White
    Write-Host "  Total NAIRA: ₦$([math]::Round($fundingData.total_naira, 2))" -ForegroundColor White
    Write-Host "  Total USDT: `$$([math]::Round($fundingData.total_usdt, 2))" -ForegroundColor White

    if ($fundingData.count -gt 0) {
        Write-Host ""
        Write-Host "  Details:" -ForegroundColor Gray
        foreach ($req in $fundingData.requests) {
            Write-Host "    - $($req.username): $($req.currency) $($req.amount_remaining) (Opted In: $($req.opted_in))" -ForegroundColor Gray
        }
    }

    Write-Host ""
    Write-Host "Withdrawal Requests:" -ForegroundColor Yellow
    Write-Host "  Count: $($withdrawalData.count)" -ForegroundColor White
    Write-Host "  Total NAIRA: ₦$([math]::Round($withdrawalData.total_naira, 2))" -ForegroundColor White
    Write-Host "  Total USDT: `$$([math]::Round($withdrawalData.total_usdt, 2))" -ForegroundColor White

    if ($withdrawalData.count -gt 0) {
        Write-Host ""
        Write-Host "  Details:" -ForegroundColor Gray
        foreach ($req in $withdrawalData.requests) {
            Write-Host "    - $($req.username): $($req.currency) $($req.amount_remaining) (Opted In: $($req.opted_in))" -ForegroundColor Gray
        }
    }

    Write-Host ""

    if ($fundingData.count -eq 0 -and $withdrawalData.count -eq 0) {
        Write-Host "[INFO] No pending requests found. Create some funding and withdrawal requests first!" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "To test the merge system:" -ForegroundColor White
        Write-Host "  1. Create a funding request (user wants to deposit money)" -ForegroundColor White
        Write-Host "  2. Create a withdrawal request (user wants to withdraw money)" -ForegroundColor White
        Write-Host "  3. Run this script again to trigger the merge" -ForegroundColor White
        exit 0
    }

} catch {
    Write-Host "[ERROR] Failed to fetch pending requests: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Step 2: Trigger Manual Merge" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$continue = Read-Host "Do you want to trigger a merge now? (Y/N)"

if ($continue -ne "Y" -and $continue -ne "y") {
    Write-Host "Merge cancelled by user." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "Triggering merge cycle..." -ForegroundColor Yellow

try {
    $mergeResponse = Invoke-RestMethod -Uri "http://localhost:8004/demo/trigger-merge" -Headers $headers -Method Post

    Write-Host "[OK] Merge completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Merge Results:" -ForegroundColor Yellow
    Write-Host ($mergeResponse.data | ConvertTo-Json -Depth 10)

} catch {
    Write-Host "[ERROR] Merge failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Test Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Check the dashboard to see matched requests" -ForegroundColor White
Write-Host "  2. Upload payment proof for matched pairs" -ForegroundColor White
Write-Host "  3. Admin can confirm completion" -ForegroundColor White
Write-Host ""
Write-Host "** Remember to remove demo endpoints before production! **" -ForegroundColor Red
Write-Host ""
