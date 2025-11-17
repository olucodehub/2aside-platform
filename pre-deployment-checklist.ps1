# ========================================
# 2-Aside Pre-Deployment Checklist Script
# ========================================
# Run this before deploying to production
# ========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  2-Aside Pre-Deployment Checklist" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$issues = @()
$warnings = @()

# Check 1: Demo endpoints
Write-Host "[1/10] Checking for demo endpoints..." -ForegroundColor Yellow
$demoEndpoints = Select-String -Path "C:\Dev\Rendezvous\2-Aside\funding-service\main.py" -Pattern "@app\.(post|get)\(`"/demo" -Quiet
if ($demoEndpoints) {
    $issues += "❌ Demo endpoints found in funding-service/main.py (lines 1708-1829)"
} else {
    Write-Host "  ✅ No demo endpoints found" -ForegroundColor Green
}

# Check 2: Test files
Write-Host "[2/10] Checking for test files..." -ForegroundColor Yellow
$testFiles = @(
    "C:\Dev\Rendezvous\test-merge-demo.ps1",
    "C:\Dev\Rendezvous\MERGE_DEMO_TESTING.md",
    "C:\Dev\Rendezvous\FUNDING_ERROR_FIX.md",
    "C:\Dev\Rendezvous\FUNDING_REQUEST_FIX.md"
)

foreach ($file in $testFiles) {
    if (Test-Path $file) {
        $issues += "❌ Test file exists: $(Split-Path $file -Leaf)"
    }
}

if ($issues.Count -eq 0 -or $issues[-1] -notlike "*Test file*") {
    Write-Host "  ✅ No test files found" -ForegroundColor Green
}

# Check 3: Debug/console.log statements
Write-Host "[3/10] Checking for debug statements..." -ForegroundColor Yellow
$debugLogs = Get-ChildItem -Path "C:\Dev\Rendezvous\2aside-frontend" -Recurse -Filter "*.tsx" |
    Select-String -Pattern "console\.(log|debug)" |
    Select-Object -First 5

if ($debugLogs) {
    $warnings += "⚠️  console.log statements found in frontend (review and remove)"
}

# Check 4: Hardcoded passwords/secrets
Write-Host "[4/10] Checking for hardcoded secrets..." -ForegroundColor Yellow
$secrets = Get-ChildItem -Path "C:\Dev\Rendezvous\2-Aside" -Recurse -Filter "*.py" |
    Select-String -Pattern "password\s*=\s*[`"'](?!<|{{)" |
    Where-Object { $_.Line -notmatch "# " } |
    Select-Object -First 3

if ($secrets) {
    $issues += "❌ Potential hardcoded passwords found in Python files"
}

# Check 5: CORS configuration
Write-Host "[5/10] Checking CORS configuration..." -ForegroundColor Yellow
$corsWildcard = Get-ChildItem -Path "C:\Dev\Rendezvous\2-Aside" -Recurse -Filter "*.py" |
    Select-String -Pattern 'allow_origins=\["?\*"?\]' -Quiet

if ($corsWildcard) {
    $issues += "❌ CORS allows all origins (*) - must restrict to production domain"
} else {
    Write-Host "  ✅ CORS not using wildcard" -ForegroundColor Green
}

# Check 6: Database connection strings
Write-Host "[6/10] Checking database connections..." -ForegroundColor Yellow
$dbStrings = Get-ChildItem -Path "C:\Dev\Rendezvous\2-Aside" -Recurse -Filter "*.py" |
    Select-String -Pattern "localhost|127\.0\.0\.1" |
    Where-Object { $_.Line -match "database|connection" }

if ($dbStrings) {
    $warnings += "⚠️  Localhost database connections found - ensure environment variables used"
}

# Check 7: Environment files
Write-Host "[7/10] Checking environment files..." -ForegroundColor Yellow
$envFiles = Get-ChildItem -Path "C:\Dev\Rendezvous" -Recurse -Filter ".env*" |
    Where-Object { $_.Name -ne ".env.example" }

if ($envFiles) {
    $warnings += "⚠️  .env files found - ensure they're in .gitignore and not committed"
}

# Check 8: Git status
Write-Host "[8/10] Checking git status..." -ForegroundColor Yellow
try {
    cd "C:\Dev\Rendezvous"
    $gitStatus = git status --porcelain 2>$null
    if ($gitStatus) {
        $warnings += "⚠️  Uncommitted changes found in git"
    } else {
        Write-Host "  ✅ Git working directory clean" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠️  Not a git repository or git not available" -ForegroundColor Yellow
}

# Check 9: Dependencies
Write-Host "[9/10] Checking for requirements.txt..." -ForegroundColor Yellow
$services = @("api-gateway", "auth-service", "wallet-service", "user-service", "funding-service")
$missingReqs = @()

foreach ($service in $services) {
    $reqFile = "C:\Dev\Rendezvous\2-Aside\$service\requirements.txt"
    if (-not (Test-Path $reqFile)) {
        $missingReqs += $service
    }
}

if ($missingReqs.Count -gt 0) {
    $warnings += "⚠️  Missing requirements.txt for: $($missingReqs -join ', ')"
} else {
    Write-Host "  ✅ All services have requirements.txt" -ForegroundColor Green
}

# Check 10: Frontend build
Write-Host "[10/10] Checking frontend build..." -ForegroundColor Yellow
if (Test-Path "C:\Dev\Rendezvous\2aside-frontend\package.json") {
    Write-Host "  ✅ Frontend package.json exists" -ForegroundColor Green
} else {
    $issues += "❌ Frontend package.json not found"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Checklist Results" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Display issues
if ($issues.Count -gt 0) {
    Write-Host "CRITICAL ISSUES (must fix before deployment):" -ForegroundColor Red
    Write-Host ""
    foreach ($issue in $issues) {
        Write-Host "  $issue" -ForegroundColor Red
    }
    Write-Host ""
}

# Display warnings
if ($warnings.Count -gt 0) {
    Write-Host "WARNINGS (review before deployment):" -ForegroundColor Yellow
    Write-Host ""
    foreach ($warning in $warnings) {
        Write-Host "  $warning" -ForegroundColor Yellow
    }
    Write-Host ""
}

# Summary
if ($issues.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✅ All checks passed! Ready for deployment." -ForegroundColor Green
} elseif ($issues.Count -eq 0) {
    Write-Host "⚠️  All critical checks passed, but review warnings." -ForegroundColor Yellow
} else {
    Write-Host "❌ Critical issues found. Fix before deploying!" -ForegroundColor Red
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Fix all critical issues listed above" -ForegroundColor White
Write-Host "  2. Review and address warnings" -ForegroundColor White
Write-Host "  3. Read PRODUCTION_DEPLOYMENT_GUIDE.md" -ForegroundColor White
Write-Host "  4. Set up staging environment first" -ForegroundColor White
Write-Host "  5. Test thoroughly before production" -ForegroundColor White
Write-Host ""
