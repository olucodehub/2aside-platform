# 2-Aside Production Deployment Guide

**Date:** November 7, 2025
**Status:** Pre-Production
**Target:** Cloud Deployment (Azure Recommended)

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Deployment Options Comparison](#deployment-options-comparison)
3. [Recommended: Azure Deployment](#recommended-azure-deployment)
4. [Alternative: AWS Deployment](#alternative-aws-deployment)
5. [Database Migration](#database-migration)
6. [Security Hardening](#security-hardening)
7. [Environment Configuration](#environment-configuration)
8. [CI/CD Pipeline](#cicd-pipeline)
9. [Monitoring & Logging](#monitoring--logging)
10. [Cost Estimates](#cost-estimates)
11. [Post-Deployment Tasks](#post-deployment-tasks)

---

## Pre-Deployment Checklist

### Code Cleanup

- [ ] **Remove demo endpoints** from `funding-service/main.py` (lines 1708-1829)
- [ ] **Delete test files:**
  - `test-merge-demo.ps1`
  - `MERGE_DEMO_TESTING.md`
  - `FUNDING_ERROR_FIX.md`
  - `FUNDING_REQUEST_FIX.md`
- [ ] **Search for debug code:** `git grep -i "demo\|test\|debug\|TODO\|FIXME"`
- [ ] **Remove hardcoded credentials** (if any)
- [ ] **Review all console.log statements** in frontend

### Security Audit

- [ ] **Change all default passwords** (admin accounts, database)
- [ ] **Generate production secrets:**
  - JWT secret keys
  - Database connection strings
  - API keys
- [ ] **Enable HTTPS only** (no HTTP)
- [ ] **Configure CORS** for production domain
- [ ] **Review file upload security** (size limits, file types)
- [ ] **Enable rate limiting** on all endpoints
- [ ] **SQL injection review** (using parameterized queries)
- [ ] **XSS protection review**

### Testing

- [ ] **Run all tests** (if you have test suite)
- [ ] **Load testing** (simulate 100+ concurrent users)
- [ ] **Security scan** (OWASP ZAP or similar)
- [ ] **Mobile responsiveness** check
- [ ] **Cross-browser testing** (Chrome, Firefox, Safari, Edge)
- [ ] **Payment flow end-to-end** test

### Documentation

- [ ] **API documentation** up to date (Swagger/OpenAPI)
- [ ] **User manual** or help documentation
- [ ] **Admin manual** for operations
- [ ] **Runbook** for common issues
- [ ] **Disaster recovery plan**

---

## Deployment Options Comparison

| Feature | Azure | AWS | DigitalOcean | Heroku |
|---------|-------|-----|--------------|--------|
| **SQL Server Support** | ⭐⭐⭐⭐⭐ Native | ⭐⭐⭐⭐ RDS | ⭐⭐ Self-managed | ⭐⭐ Add-on |
| **Nigeria Latency** | ⭐⭐⭐⭐ (South Africa DC) | ⭐⭐⭐⭐ (Cape Town) | ⭐⭐⭐ | ⭐⭐ |
| **Ease of Setup** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Scalability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Cost (Startup)** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **DevOps Tools** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Startup Credits** | ⭐⭐⭐⭐ ($200) | ⭐⭐⭐⭐ ($5K) | ⭐⭐⭐ ($200) | ⭐⭐ |

**Recommendation:** **Azure** for seamless SQL Server integration and African presence.

---

## Recommended: Azure Deployment

### Architecture Overview

```
Internet → Azure Front Door → App Services (Frontend + Backend) → Azure SQL → Key Vault
                                       ↓
                               Application Insights
```

### Step-by-Step Azure Deployment

#### 1. Create Azure Account
```bash
# Sign up at https://azure.microsoft.com/free/
# Get $200 free credit for 30 days
# Apply for startup credits: https://www.microsoft.com/startups
```

#### 2. Provision Resources

**a) Resource Group**
```bash
az group create \
  --name rg-2aside-prod \
  --location southafricawest
```

**b) Azure SQL Database**
```bash
# Create SQL Server
az sql server create \
  --name sql-2aside-prod \
  --resource-group rg-2aside-prod \
  --location southafricawest \
  --admin-user sqladmin \
  --admin-password <STRONG_PASSWORD>

# Create Database
az sql db create \
  --resource-group rg-2aside-prod \
  --server sql-2aside-prod \
  --name 2aside-production \
  --service-objective S1 \
  --backup-storage-redundancy Zone
```

**c) App Service Plan**
```bash
az appservice plan create \
  --name asp-2aside-prod \
  --resource-group rg-2aside-prod \
  --location southafricawest \
  --sku P1V2 \
  --is-linux
```

**d) Backend Services (API Gateway, Auth, Wallet, User, Funding)**
```bash
# API Gateway
az webapp create \
  --name app-2aside-gateway \
  --resource-group rg-2aside-prod \
  --plan asp-2aside-prod \
  --runtime "PYTHON:3.9"

# Repeat for auth-service, wallet-service, user-service, funding-service
```

**e) Frontend (Next.js)**
```bash
# Option 1: Azure Static Web Apps (Recommended for Next.js)
az staticwebapp create \
  --name stapp-2aside-frontend \
  --resource-group rg-2aside-prod \
  --location southafricawest \
  --sku Standard

# Option 2: Azure App Service (if you need server-side rendering)
az webapp create \
  --name app-2aside-frontend \
  --resource-group rg-2aside-prod \
  --plan asp-2aside-prod \
  --runtime "NODE:18"
```

**f) Key Vault (Secrets Management)**
```bash
az keyvault create \
  --name kv-2aside-prod \
  --resource-group rg-2aside-prod \
  --location southafricawest \
  --enable-rbac-authorization
```

**g) Application Insights (Monitoring)**
```bash
az monitor app-insights component create \
  --app ai-2aside-prod \
  --resource-group rg-2aside-prod \
  --location southafricawest
```

#### 3. Configure Database Connection

```python
# In each backend service, use Azure SQL connection string
import os
from sqlalchemy import create_engine

DATABASE_URL = os.environ.get("AZURE_SQL_CONNECTION_STRING")
# Format: mssql+pyodbc://user:password@server.database.windows.net/database?driver=ODBC+Driver+17+for+SQL+Server

engine = create_engine(DATABASE_URL)
```

#### 4. Deploy Backend Services

**Create `azure-deploy.sh` script:**
```bash
#!/bin/bash
# Deploy all backend services to Azure

RESOURCE_GROUP="rg-2aside-prod"

# API Gateway
cd 2-Aside/api-gateway
zip -r api-gateway.zip .
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name app-2aside-gateway \
  --src api-gateway.zip

# Auth Service
cd ../auth-service
zip -r auth-service.zip .
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name app-2aside-auth \
  --src auth-service.zip

# Wallet Service
cd ../wallet-service
zip -r wallet-service.zip .
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name app-2aside-wallet \
  --src wallet-service.zip

# User Service
cd ../user-service
zip -r user-service.zip .
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name app-2aside-user \
  --src user-service.zip

# Funding Service
cd ../funding-service
zip -r funding-service.zip .
az webapp deployment source config-zip \
  --resource-group $RESOURCE_GROUP \
  --name app-2aside-funding \
  --src funding-service.zip
```

#### 5. Deploy Frontend

**For Azure Static Web Apps:**
```bash
cd 2aside-frontend

# Build production
npm run build

# Deploy
az staticwebapp deploy \
  --name stapp-2aside-frontend \
  --resource-group rg-2aside-prod \
  --app-location "." \
  --output-location "out"
```

#### 6. Configure Environment Variables

**Store secrets in Key Vault:**
```bash
# JWT Secret
az keyvault secret set \
  --vault-name kv-2aside-prod \
  --name JWT-SECRET-KEY \
  --value <YOUR_SECRET>

# Database Connection
az keyvault secret set \
  --vault-name kv-2aside-prod \
  --name SQL-CONNECTION-STRING \
  --value <YOUR_CONNECTION_STRING>
```

**Configure App Services to use Key Vault:**
```bash
az webapp config appsettings set \
  --resource-group rg-2aside-prod \
  --name app-2aside-gateway \
  --settings \
    JWT_SECRET_KEY="@Microsoft.KeyVault(SecretUri=https://kv-2aside-prod.vault.azure.net/secrets/JWT-SECRET-KEY/)" \
    DATABASE_URL="@Microsoft.KeyVault(SecretUri=https://kv-2aside-prod.vault.azure.net/secrets/SQL-CONNECTION-STRING/)"
```

#### 7. Configure Custom Domain

```bash
# Add custom domain
az webapp config hostname add \
  --webapp-name app-2aside-gateway \
  --resource-group rg-2aside-prod \
  --hostname api.2aside.com

# Enable HTTPS (Azure provides free SSL cert)
az webapp config ssl bind \
  --certificate-thumbprint <THUMBPRINT> \
  --ssl-type SNI \
  --name app-2aside-gateway \
  --resource-group rg-2aside-prod
```

#### 8. Enable Auto-Scaling

```bash
az monitor autoscale create \
  --resource-group rg-2aside-prod \
  --resource app-2aside-gateway \
  --resource-type Microsoft.Web/serverFarms \
  --name autoscale-2aside \
  --min-count 2 \
  --max-count 10 \
  --count 2

# Scale on CPU > 75%
az monitor autoscale rule create \
  --autoscale-name autoscale-2aside \
  --resource-group rg-2aside-prod \
  --condition "Percentage CPU > 75 avg 5m" \
  --scale out 1
```

---

## Alternative: AWS Deployment

### Architecture Overview

```
Internet → CloudFront → ALB → ECS (Docker Containers) → RDS SQL Server → Secrets Manager
                                      ↓
                              CloudWatch Logs
```

### Key AWS Services

1. **AWS RDS for SQL Server** - Managed database
2. **AWS ECS (Fargate)** - Containerized backend services
3. **AWS Amplify or S3 + CloudFront** - Frontend hosting
4. **AWS ALB** - Load balancing
5. **AWS Secrets Manager** - Secrets storage
6. **CloudWatch** - Monitoring and logging

### Quick AWS Setup

```bash
# 1. Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# 2. Create RDS SQL Server
aws rds create-db-instance \
  --db-instance-identifier 2aside-prod-db \
  --db-instance-class db.t3.small \
  --engine sqlserver-ex \
  --master-username admin \
  --master-user-password <PASSWORD> \
  --allocated-storage 20

# 3. Create ECS Cluster
aws ecs create-cluster --cluster-name 2aside-cluster

# 4. Deploy Docker containers (requires Dockerfile for each service)
```

---

## Database Migration

### Export from Development

```powershell
# Create backup of current database
$date = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "C:\Dev\Rendezvous\backups\RendezvousDB_$date.bak"

sqlcmd -S localhost -Q "BACKUP DATABASE RendezvousDB TO DISK = '$backupFile'"
```

### Import to Azure SQL

```powershell
# Option 1: Using Azure Data Migration Service (Recommended)
# https://azure.microsoft.com/services/database-migration/

# Option 2: Using BACPAC file
SqlPackage.exe /Action:Export `
  /SourceServerName:localhost `
  /SourceDatabaseName:RendezvousDB `
  /TargetFile:C:\Dev\Rendezvous\backups\RendezvousDB.bacpac

# Import to Azure
SqlPackage.exe /Action:Import `
  /SourceFile:C:\Dev\Rendezvous\backups\RendezvousDB.bacpac `
  /TargetServerName:sql-2aside-prod.database.windows.net `
  /TargetDatabaseName:2aside-production `
  /TargetUser:sqladmin `
  /TargetPassword:<PASSWORD>
```

### Database Considerations

- **Connection Pooling:** Configure SQLAlchemy pool settings for cloud
- **Firewall Rules:** Add Azure service IPs to SQL Server firewall
- **Backup Strategy:** Enable automated daily backups
- **Point-in-Time Recovery:** Enable for disaster recovery

---

## Security Hardening

### 1. Remove Sensitive Data from Code

```bash
# Search for hardcoded secrets
grep -r "password\|secret\|key" --include="*.py" --include="*.ts" .

# Move to environment variables
```

### 2. Update CORS Configuration

**Before (Development):**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ❌ Dangerous!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**After (Production):**
```python
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # ✅ Only production domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 3. Enable Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

@app.post("/login")
@limiter.limit("5/minute")  # Max 5 login attempts per minute
async def login(request: Request, ...):
    ...
```

### 4. Implement Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Force HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# Only accept requests from trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["2aside.com", "*.2aside.com"]
)

# Add security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

### 5. Password Requirements

```python
import re

def validate_password_strength(password: str) -> bool:
    """
    Password must have:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True
```

---

## Environment Configuration

### Production `.env` File Structure

**DO NOT commit this to Git!**

```bash
# .env.production

# Database
DATABASE_URL=mssql+pyodbc://user:password@sql-2aside-prod.database.windows.net/2aside-production?driver=ODBC+Driver+17+for+SQL+Server

# JWT
JWT_SECRET_KEY=<RANDOM_256_BIT_KEY>
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# API URLs
API_GATEWAY_URL=https://api.2aside.com
AUTH_SERVICE_URL=https://auth.2aside.com
WALLET_SERVICE_URL=https://wallet.2aside.com
USER_SERVICE_URL=https://user.2aside.com
FUNDING_SERVICE_URL=https://funding.2aside.com

# Frontend
NEXT_PUBLIC_API_URL=https://api.2aside.com

# CORS
ALLOWED_ORIGINS=https://2aside.com,https://www.2aside.com

# Email (if you add email notifications)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<SENDGRID_API_KEY>

# Monitoring
APPLICATION_INSIGHTS_KEY=<AZURE_INSIGHTS_KEY>

# File Storage
AZURE_STORAGE_CONNECTION_STRING=<CONNECTION_STRING>
AZURE_STORAGE_CONTAINER_NAME=receipts
```

### Generate Secure Secrets

```python
import secrets

# JWT Secret (256-bit)
jwt_secret = secrets.token_urlsafe(32)
print(f"JWT_SECRET_KEY={jwt_secret}")

# API Keys
api_key = secrets.token_urlsafe(32)
print(f"API_KEY={api_key}")
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

Create `.github/workflows/deploy-production.yml`:

```yaml
name: Deploy to Azure Production

on:
  push:
    branches:
      - main  # Only deploy from main branch

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [api-gateway, auth-service, wallet-service, user-service, funding-service]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          cd 2-Aside/${{ matrix.service }}
          pip install -r requirements.txt

      - name: Run tests
        run: |
          cd 2-Aside/${{ matrix.service }}
          pytest tests/

      - name: Deploy to Azure
        uses: azure/webapps-deploy@v2
        with:
          app-name: app-2aside-${{ matrix.service }}
          publish-profile: ${{ secrets.AZURE_WEBAPP_PUBLISH_PROFILE }}
          package: 2-Aside/${{ matrix.service }}

  deploy-frontend:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd 2aside-frontend
          npm ci

      - name: Build
        run: |
          cd 2aside-frontend
          npm run build
        env:
          NEXT_PUBLIC_API_URL: ${{ secrets.PRODUCTION_API_URL }}

      - name: Deploy to Azure Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "2aside-frontend"
          output_location: "out"
```

---

## Monitoring & Logging

### Azure Application Insights Setup

**Backend (Python):**
```python
from opencensus.ext.azure.log_exporter import AzureLogHandler
import logging

# Configure Azure Application Insights
logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string=os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
))

# Log events
logger.info("User login successful", extra={"user_id": user_id})
logger.error("Payment processing failed", extra={"error": str(e)})
```

**Frontend (Next.js):**
```typescript
import { ApplicationInsights } from '@microsoft/applicationinsights-web'

const appInsights = new ApplicationInsights({
  config: {
    connectionString: process.env.NEXT_PUBLIC_APP_INSIGHTS_CONNECTION_STRING
  }
})

appInsights.loadAppInsights()
appInsights.trackPageView()
```

### Key Metrics to Monitor

1. **Request Rate:** Requests per second
2. **Response Time:** Average API response time (should be < 200ms)
3. **Error Rate:** Failed requests percentage (should be < 1%)
4. **Database Performance:** Query execution time
5. **Merge Cycle Success:** Percentage of successful matches
6. **User Activity:** Active users, registrations, transactions

### Alerting Rules

```bash
# Alert if error rate > 5%
az monitor metrics alert create \
  --name high-error-rate \
  --resource-group rg-2aside-prod \
  --scopes $(az webapp show --name app-2aside-gateway --resource-group rg-2aside-prod --query id -o tsv) \
  --condition "avg Http5xx > 5" \
  --window-size 5m \
  --evaluation-frequency 1m

# Alert if response time > 1 second
az monitor metrics alert create \
  --name slow-response \
  --resource-group rg-2aside-prod \
  --scopes $(az webapp show --name app-2aside-gateway --resource-group rg-2aside-prod --query id -o tsv) \
  --condition "avg ResponseTime > 1000" \
  --window-size 5m
```

---

## Cost Estimates

### Azure (Recommended Tier for MVP)

| Service | Tier | Monthly Cost (USD) |
|---------|------|-------------------|
| Azure SQL Database | S1 (20 DTU) | ~$30 |
| App Service Plan | P1V2 (5 services) | ~$150 |
| Static Web App | Standard | ~$9 |
| Application Insights | Pay-as-you-go | ~$10 (low traffic) |
| Azure Front Door | Standard | ~$35 |
| Key Vault | Standard | ~$3 |
| **Total** | | **~$237/month** |

**With 1,000 active users:**
- Database: ~$50
- Compute: ~$200
- **Total: ~$287/month**

**Savings Tips:**
- Use Azure Reserved Instances (save 40%)
- Apply for Microsoft for Startups ($5,000 credits)
- Scale down during off-peak hours

### AWS Comparison

| Service | Tier | Monthly Cost (USD) |
|---------|------|-------------------|
| RDS SQL Server | db.t3.small | ~$80 |
| ECS Fargate (5 tasks) | 0.25 vCPU, 0.5 GB | ~$120 |
| CloudFront | Pay-as-you-go | ~$20 |
| ALB | Standard | ~$20 |
| **Total** | | **~$240/month** |

---

## Post-Deployment Tasks

### Day 1: Launch Checklist

- [ ] **Smoke test all endpoints**
- [ ] **Test user registration flow**
- [ ] **Test funding request creation**
- [ ] **Test withdrawal request creation**
- [ ] **Test manual merge (if keeping demo for admin)**
- [ ] **Verify email notifications** (if implemented)
- [ ] **Test payment flow end-to-end**
- [ ] **Verify WAT timezone display**
- [ ] **Check mobile responsiveness**

### Week 1: Monitoring

- [ ] **Set up daily monitoring checks**
- [ ] **Review error logs daily**
- [ ] **Monitor database performance**
- [ ] **Track user signups**
- [ ] **Monitor transaction success rate**

### Month 1: Optimization

- [ ] **Analyze slow queries** and optimize
- [ ] **Review and optimize costs**
- [ ] **Scale resources based on usage**
- [ ] **Collect user feedback**
- [ ] **Plan feature updates**

---

## Disaster Recovery Plan

### Backup Strategy

1. **Database Backups:**
   - Automated daily backups (Azure SQL default)
   - Retain backups for 30 days
   - Test restore monthly

2. **Code Backups:**
   - Git repository (already done)
   - Mirror to second remote (GitHub + Azure DevOps)

3. **Configuration Backups:**
   - Export Key Vault secrets monthly
   - Document all environment configurations

### Incident Response

**Severity Levels:**
- **P0 (Critical):** Service completely down
- **P1 (High):** Major feature broken (e.g., payments)
- **P2 (Medium):** Minor feature broken
- **P3 (Low):** Cosmetic issues

**Response Times:**
- P0: Immediate (24/7 on-call)
- P1: Within 1 hour
- P2: Within 4 hours
- P3: Within 24 hours

### Rollback Plan

```bash
# If deployment fails, rollback to previous version
az webapp deployment slot swap \
  --name app-2aside-gateway \
  --resource-group rg-2aside-prod \
  --slot staging \
  --action swap
```

---

## Next Steps

1. **Review this guide thoroughly**
2. **Set up Azure account** (or AWS if preferred)
3. **Complete pre-deployment checklist**
4. **Run security audit**
5. **Deploy to staging environment first**
6. **Test staging thoroughly**
7. **Deploy to production**
8. **Monitor closely for first 48 hours**

---

## Additional Resources

- **Azure Documentation:** https://docs.microsoft.com/azure/
- **Azure for Startups:** https://www.microsoft.com/startups
- **Security Best Practices:** https://owasp.org/www-project-top-ten/
- **FastAPI Production:** https://fastapi.tiangolo.com/deployment/
- **Next.js Deployment:** https://nextjs.org/docs/deployment

---

**Questions or Issues?**
Document everything and maintain a runbook for common operations!
