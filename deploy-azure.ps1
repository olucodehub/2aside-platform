# Azure App Service Deployment Script for 2-Aside Platform
# This script configures all 3 services with environment variables and startup commands

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "2-Aside Platform - Azure Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Configuration
$resourceGroup = "RendezvousRG"
$userServiceApp = "twoaside-user-service"
$walletServiceApp = "twoaside-wallet-service"
$fundingServiceApp = "twoaside-funding-service"

# Database Configuration
$databaseUrl = "mssql+pyodbc://Rendezvous:Paparazi101%40@rendezvousdbserver.database.windows.net:1433/RendezvousDB?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"
$jwtSecret = "QjQXrItpmN6PVc8nzheCaNkWqWlofnr2zksc2j+z+Mk="
$jwtAlgorithm = "HS256"
$accessTokenExpire = "30"

# Azure Blob Storage Configuration (from your previous setup)
$storageAccountName = "2asidestorage"
$storageContainerName = "payment-proofs"

Write-Host "Step 1: Configuring User Service..." -ForegroundColor Yellow
Write-Host "--------------------------------------"

# Configure User Service
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $userServiceApp `
    --settings `
        DATABASE_URL="$databaseUrl" `
        JWT_SECRET_KEY="$jwtSecret" `
        JWT_ALGORITHM="$jwtAlgorithm" `
        ACCESS_TOKEN_EXPIRE_MINUTES="$accessTokenExpire"

# Set startup command for User Service
az webapp config set `
    --resource-group $resourceGroup `
    --name $userServiceApp `
    --startup-file "bash startup.sh"

Write-Host "✓ User Service configured" -ForegroundColor Green
Write-Host ""

Write-Host "Step 2: Configuring Wallet Service..." -ForegroundColor Yellow
Write-Host "--------------------------------------"

# Configure Wallet Service
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $walletServiceApp `
    --settings `
        DATABASE_URL="$databaseUrl" `
        JWT_SECRET_KEY="$jwtSecret" `
        JWT_ALGORITHM="$jwtAlgorithm" `
        USER_SERVICE_URL="https://$userServiceApp.azurewebsites.net"

# Set startup command for Wallet Service
az webapp config set `
    --resource-group $resourceGroup `
    --name $walletServiceApp `
    --startup-file "bash startup.sh"

Write-Host "✓ Wallet Service configured" -ForegroundColor Green
Write-Host ""

Write-Host "Step 3: Configuring Funding Service..." -ForegroundColor Yellow
Write-Host "--------------------------------------"

# Configure Funding Service
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $fundingServiceApp `
    --settings `
        DATABASE_URL="$databaseUrl" `
        JWT_SECRET_KEY="$jwtSecret" `
        JWT_ALGORITHM="$jwtAlgorithm" `
        USER_SERVICE_URL="https://$userServiceApp.azurewebsites.net" `
        WALLET_SERVICE_URL="https://$walletServiceApp.azurewebsites.net" `
        AZURE_STORAGE_ACCOUNT_NAME="$storageAccountName" `
        AZURE_STORAGE_CONTAINER_NAME="$storageContainerName"

# Set startup command for Funding Service
az webapp config set `
    --resource-group $resourceGroup `
    --name $fundingServiceApp `
    --startup-file "bash startup.sh"

Write-Host "✓ Funding Service configured" -ForegroundColor Green
Write-Host ""

Write-Host "Step 4: Configuring deployment sources..." -ForegroundColor Yellow
Write-Host "--------------------------------------"

# Configure GitHub deployment for User Service
az webapp deployment source config `
    --resource-group $resourceGroup `
    --name $userServiceApp `
    --repo-url https://github.com/olucodehub/2aside-platform `
    --branch main `
    --manual-integration

Write-Host "✓ User Service deployment source configured" -ForegroundColor Green

# Configure GitHub deployment for Wallet Service
az webapp deployment source config `
    --resource-group $resourceGroup `
    --name $walletServiceApp `
    --repo-url https://github.com/olucodehub/2aside-platform `
    --branch main `
    --manual-integration

Write-Host "✓ Wallet Service deployment source configured" -ForegroundColor Green

# Configure GitHub deployment for Funding Service
az webapp deployment source config `
    --resource-group $resourceGroup `
    --name $fundingServiceApp `
    --repo-url https://github.com/olucodehub/2aside-platform `
    --branch main `
    --manual-integration

Write-Host "✓ Funding Service deployment source configured" -ForegroundColor Green
Write-Host ""

Write-Host "Step 5: Setting deployment paths..." -ForegroundColor Yellow
Write-Host "--------------------------------------"

# Set deployment path for User Service
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $userServiceApp `
    --settings `
        PROJECT="2-Aside/user-service"

Write-Host "✓ User Service deployment path set" -ForegroundColor Green

# Set deployment path for Wallet Service
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $walletServiceApp `
    --settings `
        PROJECT="2-Aside/wallet-service"

Write-Host "✓ Wallet Service deployment path set" -ForegroundColor Green

# Set deployment path for Funding Service
az webapp config appsettings set `
    --resource-group $resourceGroup `
    --name $fundingServiceApp `
    --settings `
        PROJECT="2-Aside/funding-service"

Write-Host "✓ Funding Service deployment path set" -ForegroundColor Green
Write-Host ""

Write-Host "Step 6: Starting all services..." -ForegroundColor Yellow
Write-Host "--------------------------------------"

# Start User Service
az webapp start --resource-group $resourceGroup --name $userServiceApp
Write-Host "✓ User Service started" -ForegroundColor Green

# Start Wallet Service
az webapp start --resource-group $resourceGroup --name $walletServiceApp
Write-Host "✓ Wallet Service started" -ForegroundColor Green

# Start Funding Service
az webapp start --resource-group $resourceGroup --name $fundingServiceApp
Write-Host "✓ Funding Service started" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Your services are now running at:" -ForegroundColor White
Write-Host "  User Service:    https://$userServiceApp.azurewebsites.net" -ForegroundColor Cyan
Write-Host "  Wallet Service:  https://$walletServiceApp.azurewebsites.net" -ForegroundColor Cyan
Write-Host "  Funding Service: https://$fundingServiceApp.azurewebsites.net" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Wait 2-3 minutes for services to fully start"
Write-Host "2. Test the health endpoints:"
Write-Host "   curl https://$userServiceApp.azurewebsites.net/health"
Write-Host "3. Check logs if any service fails:"
Write-Host "   az webapp log tail --resource-group $resourceGroup --name $userServiceApp"
Write-Host ""
