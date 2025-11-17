# Azure Container Apps Deployment Guide - 2-Aside Platform

## Complete Step-by-Step Deployment for Progressive Beta Testing

This guide will walk you through deploying the 2-Aside platform using Azure Container Apps with automatic CI/CD from GitHub.

---

## Why Azure Container Apps?

- **Cost-Effective**: Pay only for what you use (~$5-30/month for beta)
- **Auto-Scaling**: Scales from 0 to handle traffic spikes
- **Container-Based**: Uses your Docker files
- **Built-in CI/CD**: Auto-deploy from GitHub
- **Multiple Services**: Easy to manage 3+ services
- **Managed Infrastructure**: No server management

---

## Prerequisites

Before you begin, ensure you have:

- [ ] Azure account (sign up at https://azure.com - free tier available)
- [ ] GitHub account
- [ ] Code pushed to GitHub repository
- [ ] Azure Blob Storage set up (follow AZURE_SETUP_INSTRUCTIONS.md)
- [ ] SQL Server database accessible from internet OR Azure SQL Database

---

## Part 1: Prepare Your Code

### Step 1: Create .env.example Template

Create `2-Aside/.env.example`:

```env
# Database Configuration
DATABASE_URL=mssql+pyodbc://username:password@server:1433/RendezvousDB?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-min-32-characters-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=payment-proofs
```

### Step 2: Push to GitHub

```bash
cd C:\Dev\Rendezvous
git add .
git commit -m "Prepare for Azure Container Apps deployment"
git push origin main
```

---

## Part 2: Set Up Azure Resources

### Step 1: Create Resource Group

1. **Go to Azure Portal**: https://portal.azure.com
2. **Click "Resource groups"** → "+ Create"
3. **Fill in details**:
   - Subscription: Your subscription
   - Resource group: `2aside-resources`
   - Region: Choose closest to Nigeria (e.g., "South Africa North" or "West Europe")
4. **Click "Review + Create"** → "Create"

### Step 2: Create Container Registry (ACR)

This stores your Docker images.

1. **Search** for "Container registries" → "+ Create"
2. **Fill in details**:
   - Resource group: `2aside-resources`
   - Registry name: `2asideregistry` (must be globally unique, lowercase only)
   - Location: Same as resource group
   - SKU: **Basic** ($5/month)
3. **Review + Create** → "Create"
4. **After deployment**, go to the registry:
   - Left menu → "Access keys"
   - Enable "Admin user"
   - **Copy**: Login server, Username, Password (save these!)

### Step 3: Create Container App Environment

This is the "hosting environment" for your containers.

1. **Search** for "Container Apps" → "+ Create"
2. **Basics tab**:
   - Resource group: `2aside-resources`
   - Container app name: `2aside-user-service`
   - Region: Same as before
3. **Container Apps Environment**:
   - Click "Create new"
   - Environment name: `2aside-environment`
   - Zone redundancy: Disabled (for cost savings)
   - Click "Create"
4. **Container tab** (we'll configure this per service):
   - Skip for now, we'll use GitHub Actions
5. **Click "Review + create"** → "Create"

---

## Part 3: Deploy Services Using GitHub Actions

### Step 1: Set Up GitHub Secrets

1. **Go to your GitHub repository**
2. **Settings** → "Secrets and variables" → "Actions"
3. **Click "New repository secret"** and add these secrets:

| Secret Name | Value |
|------------|-------|
| `AZURE_CREDENTIALS` | (We'll get this in next step) |
| `REGISTRY_LOGIN_SERVER` | `2asideregistry.azurecr.io` |
| `REGISTRY_USERNAME` | From ACR Access keys |
| `REGISTRY_PASSWORD` | From ACR Access keys password |
| `DATABASE_URL` | Your full database connection string |
| `JWT_SECRET` | Generate random 32+ character string |
| `AZURE_STORAGE_CONNECTION_STRING` | From Azure Blob Storage |
| `AZURE_STORAGE_CONTAINER_NAME` | `payment-proofs` |

### Step 2: Get Azure Credentials

Run this in Azure Cloud Shell (portal.azure.com → click cloud shell icon):

```bash
az ad sp create-for-rbac \
  --name "2aside-github-deploy" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/2aside-resources \
  --sdk-auth
```

**Replace `{subscription-id}`** with your subscription ID (find in Azure Portal → Subscriptions).

**Copy the entire JSON output** and add it as `AZURE_CREDENTIALS` secret in GitHub.

### Step 3: Create GitHub Actions Workflows

Create `.github/workflows/deploy-user-service.yml`:

```yaml
name: Deploy User Service

on:
  push:
    branches: [ main ]
    paths:
      - '2-Aside/user-service/**'
      - '2-Aside/shared/**'
      - '.github/workflows/deploy-user-service.yml'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Login to Azure Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ secrets.REGISTRY_LOGIN_SERVER }}
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}

    - name: Build and push Docker image
      working-directory: ./2-Aside
      run: |
        docker build -f user-service/Dockerfile \
          -t ${{ secrets.REGISTRY_LOGIN_SERVER }}/user-service:${{ github.sha }} \
          -t ${{ secrets.REGISTRY_LOGIN_SERVER }}/user-service:latest \
          .
        docker push ${{ secrets.REGISTRY_LOGIN_SERVER }}/user-service:${{ github.sha }}
        docker push ${{ secrets.REGISTRY_LOGIN_SERVER }}/user-service:latest

    - name: Login to Azure
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Deploy to Azure Container Apps
      uses: azure/container-apps-deploy-action@v1
      with:
        containerAppName: 2aside-user-service
        resourceGroup: 2aside-resources
        imageToDeploy: ${{ secrets.REGISTRY_LOGIN_SERVER }}/user-service:${{ github.sha }}
        environmentVariables: |
          DATABASE_URL=secretref:database-url
          JWT_SECRET=secretref:jwt-secret
          JWT_ALGORITHM=HS256
          ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Create similar files for:
- `.github/workflows/deploy-wallet-service.yml` (change paths and names)
- `.github/workflows/deploy-funding-service.yml` (change paths and names, add Azure storage env vars)

### Step 4: Configure Container Apps Secrets

For each service, add secrets in Azure Portal:

1. **Go to Container App** (e.g., 2aside-user-service)
2. **Left menu** → "Secrets"
3. **Add secrets**:
   - `database-url`: Your DATABASE_URL
   - `jwt-secret`: Your JWT_SECRET
   - `azure-storage-connection-string`: (for funding service only)
   - `azure-storage-container-name`: `payment-proofs` (for funding service)

### Step 5: Trigger Deployment

```bash
git add .
git commit -m "Add GitHub Actions workflows"
git push origin main
```

**GitHub Actions will automatically**:
1. Build Docker images
2. Push to Azure Container Registry
3. Deploy to Azure Container Apps

**Monitor progress**: GitHub repo → Actions tab

---

## Part 4: Configure Networking & Ingress

### Step 1: Enable HTTP Ingress

For each Container App:

1. **Go to Container App** → "Ingress"
2. **Enable ingress**: Yes
3. **Ingress traffic**: Accepting traffic from anywhere
4. **Ingress type**: HTTP
5. **Target port**: `8000`
6. **Click "Save"**

You'll get a URL like: `https://2aside-user-service.{random}.{region}.azurecontainerapps.io`

### Step 2: Test Endpoints

```bash
# Test user service
curl https://2aside-user-service.{random}.{region}.azurecontainerapps.io/health

# Expected: {"status": "ok"}
```

---

## Part 5: Deploy Frontend to Vercel

### Step 1: Update Frontend Environment Variables

Create `2aside-frontend/.env.production`:

```env
NEXT_PUBLIC_API_URL=https://2aside-funding-service.{random}.{region}.azurecontainerapps.io
NEXT_PUBLIC_USER_SERVICE_URL=https://2aside-user-service.{random}.{region}.azurecontainerapps.io
NEXT_PUBLIC_WALLET_SERVICE_URL=https://2aside-wallet-service.{random}.{region}.azurecontainerapps.io
```

### Step 2: Deploy to Vercel

1. **Go to** https://vercel.com
2. **Import project** from GitHub
3. **Select** `2aside-frontend` directory
4. **Add environment variables** (from `.env.production`)
5. **Deploy**

**Your app is now live!** URL: `https://2aside-{random}.vercel.app`

### Step 3: Update Backend CORS

Update CORS in all backend services (`main.py`):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://2aside-{random}.vercel.app",  # Your Vercel URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Push changes** → GitHub Actions redeploys automatically!

---

## Part 6: Set Up Custom Domain (Optional)

### Step 1: Add Custom Domain to Vercel

1. **Vercel dashboard** → Your project → Settings → Domains
2. **Add domain**: `yourdomain.com`
3. **Follow DNS instructions** to verify ownership

### Step 2: Update CORS with Custom Domain

Update backend CORS to include your custom domain.

---

## Cost Breakdown

### Beta Testing (~100 users, light usage):

| Service | Cost/Month |
|---------|-----------|
| Azure Container Registry (Basic) | $5 |
| Azure Container Apps (3 services, ~500K requests) | $10-20 |
| Azure Blob Storage (5GB) | $1 |
| Azure SQL Database (Basic) | $5 |
| Vercel (Free tier) | $0 |
| **Total** | **~$20-30/month** |

### Production (1000+ users):

| Service | Cost/Month |
|---------|-----------|
| Azure Container Registry (Standard) | $20 |
| Azure Container Apps (auto-scaled) | $50-100 |
| Azure Blob Storage (50GB) | $5 |
| Azure SQL Database (Standard S1) | $30 |
| Vercel Pro (optional) | $20 |
| **Total** | **~$125-175/month** |

---

## Part 7: Monitoring & Logs

### View Logs

1. **Azure Portal** → Container App
2. **Left menu** → "Log stream"
3. **See real-time logs**

### Set Up Alerts

1. **Container App** → "Alerts"
2. **New alert rule**:
   - Signal: HTTP 5xx errors
   - Threshold: > 10 in 5 minutes
   - Action: Email notification

### Application Insights (Recommended)

1. **Create Application Insights** resource
2. **Add to Container Apps** environment variables:
   ```
   APPLICATIONINSIGHTS_CONNECTION_STRING=your_connection_string
   ```
3. **View metrics**: Requests, failures, response times

---

## Part 8: Progressive Updates Workflow

### Development → Production Flow:

1. **Make changes locally**
2. **Test locally**: `docker-compose up`
3. **Push to GitHub**: `git push origin main`
4. **GitHub Actions auto-deploys** to Azure
5. **Vercel auto-deploys** frontend
6. **Beta testers get updates** automatically (30 sec - 2 min)

### Rollback Strategy:

If deployment fails or has bugs:

1. **Azure Portal** → Container App → "Revisions"
2. **See all deployments** (each GitHub push = new revision)
3. **Click previous revision** → "Activate"
4. **Instant rollback** to previous working version

---

## Troubleshooting

### Container won't start:
- Check logs in Azure Portal
- Verify environment variables are set correctly
- Test Docker image locally: `docker run -p 8000:8000 your-image`

### Database connection errors:
- Verify SQL Server firewall allows Azure services
- Check connection string format
- Test connection from local machine first

### GitHub Actions fails:
- Check secrets are set correctly (no extra spaces)
- Verify Azure credentials have correct permissions
- Check Docker build logs for errors

### CORS errors in browser:
- Verify Vercel URL is in backend CORS allow_origins
- Check protocol (http vs https)
- Clear browser cache

---

## Security Best Practices

- [ ] Use Azure Key Vault for secrets (production)
- [ ] Enable Azure SQL Database firewall rules
- [ ] Rotate JWT secret periodically
- [ ] Enable HTTPS only (automatic with Container Apps)
- [ ] Set up rate limiting on Container Apps
- [ ] Regular security updates: `pip list --outdated`
- [ ] Enable Azure DDoS protection (production)
- [ ] Use managed identity instead of connection strings (advanced)

---

## Next Steps

1. ✅ Set up Azure resources (Resource Group, ACR, Container Apps Environment)
2. ✅ Configure GitHub secrets
3. ✅ Create GitHub Actions workflows
4. ✅ Deploy backend services
5. ✅ Deploy frontend to Vercel
6. ✅ Test end-to-end flow
7. ⬜ Share with beta testers
8. ⬜ Monitor usage and performance
9. ⬜ Iterate based on feedback

---

## Support Resources

- **Azure Container Apps Docs**: https://docs.microsoft.com/azure/container-apps/
- **GitHub Actions Docs**: https://docs.github.com/actions
- **Vercel Docs**: https://vercel.com/docs
- **Docker Docs**: https://docs.docker.com/

---

## Quick Reference Commands

### Local Testing with Docker:
```bash
cd 2-Aside
docker-compose -f docker-compose.prod.yml up --build
```

### View Container Logs (Azure CLI):
```bash
az containerapp logs show \
  --name 2aside-user-service \
  --resource-group 2aside-resources \
  --follow
```

### Manual Deploy (Azure CLI):
```bash
az containerapp up \
  --name 2aside-user-service \
  --resource-group 2aside-resources \
  --image 2asideregistry.azurecr.io/user-service:latest
```

---

## Mobile Access

Your app is now accessible on mobile devices:

1. **Share URL**: `https://2aside-{random}.vercel.app`
2. **Works on**: All mobile browsers (iOS Safari, Chrome, etc.)
3. **Install as PWA**: Users can add to home screen
4. **Responsive**: Already mobile-optimized from Next.js

**No app store submission needed!**

---

## Congratulations!

Your 2-Aside platform is now deployed and ready for progressive beta testing. Every time you push code to GitHub, your services automatically update in production. Beta testers will always have the latest version!
