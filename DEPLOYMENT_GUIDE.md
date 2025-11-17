# Progressive Deployment Guide - 2-Aside Platform

## Overview

This guide will help you deploy the 2-Aside platform for progressive beta testing with mobile access.

**Recommended Stack:**
- Frontend: Vercel (Free tier, instant deployments)
- Backend: Azure App Service (Python)
- Database: Azure SQL Database (or keep existing SQL Server accessible)
- Storage: Azure Blob Storage (payment proofs)

**Benefits:**
- Mobile-responsive (works on all phones/tablets)
- Continuous deployment (push code → live in minutes)
- Free SSL certificates
- Progressive testing (beta testers get updates instantly)
- Cost: ~$15-40/month during beta

---

## Part 1: Azure Blob Storage Setup (Required First)

### Step 1: Create Azure Storage Account

1. **Go to Azure Portal**: https://portal.azure.com
2. **Create Storage Account**:
   - Click "Create a resource" → Search "Storage account"
   - **Subscription**: Your Azure subscription
   - **Resource Group**: Create new "2aside-resources"
   - **Storage account name**: `2asidestorage` (must be globally unique, lowercase, no special chars)
   - **Region**: Choose closest to Nigeria (e.g., "South Africa North" or "West Europe")
   - **Performance**: Standard
   - **Redundancy**: LRS (Locally Redundant Storage) for beta, GRS for production
3. **Review + Create** → Wait for deployment (~2 minutes)

### Step 2: Get Connection String

1. Go to your new Storage Account
2. Left menu: **"Access keys"** under Security + networking
3. Click **"Show"** next to Connection string for key1
4. **Copy the entire connection string** (starts with `DefaultEndpointsProtocol=https...`)

### Step 3: Configure Local Environment

1. Navigate to `C:\Dev\Rendezvous\2-Aside\funding-service\`
2. Create a `.env` file (use `.env.example` as template)
3. Paste your connection string:

```env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=2asidestorage;AccountKey=YOUR_KEY_HERE;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=payment-proofs
```

### Step 4: Test Locally

1. Restart your funding service
2. Check console for: `[OK] Using existing blob container: payment-proofs`
3. Test payment proof upload - check Azure Portal → Storage Account → Containers → payment-proofs

---

## Part 2: Database Setup

### Option A: Keep Existing SQL Server (Easiest for Testing)

1. **Make SQL Server accessible from internet**:
   - Enable SQL Server Authentication
   - Configure firewall to allow Azure services
   - Use static IP or dynamic DNS
   - **Security**: Change default port 1433, use strong passwords

2. **Connection string format**:
```
Server=YOUR_IP_OR_DOMAIN,1433;Database=RendezvousDB;User Id=sa;Password=YOUR_PASSWORD;Encrypt=yes;TrustServerCertificate=yes;
```

### Option B: Migrate to Azure SQL Database (Recommended for Production)

1. **Create Azure SQL Database**:
   - Portal → Create resource → "SQL Database"
   - Database name: `RendezvousDB`
   - Server: Create new server
   - Pricing tier: Basic ($5/month) for beta testing

2. **Migrate existing database**:
   - Use SQL Server Management Studio
   - Right-click database → Tasks → Deploy to Azure SQL Database
   - Follow wizard

3. **Get connection string**:
   - Azure Portal → SQL Database → Connection strings
   - Copy the ADO.NET connection string

---

## Part 3: Backend Deployment (Azure App Service)

### Step 1: Prepare Backend for Deployment

1. **Create `startup.sh` in `2-Aside/funding-service/`**:

```bash
#!/bin/bash
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

2. **Update CORS in `main.py`** (add production domains):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-app.vercel.app",  # Add after frontend deployment
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 2: Deploy Backend to Azure

#### Option A: Deploy via Azure Portal (Easiest)

1. **Create App Service**:
   - Azure Portal → Create resource → "Web App"
   - **Name**: `2aside-api` (becomes 2aside-api.azurewebsites.net)
   - **Runtime**: Python 3.9
   - **Region**: Same as storage account
   - **Pricing**: Basic B1 (~$13/month) or Free F1 for testing

2. **Configure environment variables**:
   - Go to App Service → Configuration → Application settings
   - Add these settings:
     - `AZURE_STORAGE_CONNECTION_STRING`: [your connection string]
     - `AZURE_STORAGE_CONTAINER_NAME`: payment-proofs
     - `DATABASE_URL`: [your database connection string]
     - `JWT_SECRET`: [generate random 32-character string]

3. **Deploy code**:
   - App Service → Deployment Center
   - Source: GitHub (connect your repo)
   - Branch: main
   - Build provider: GitHub Actions
   - Save → Auto-deploys on every push

#### Option B: Deploy via VS Code (Faster)

1. Install Azure App Service extension in VS Code
2. Right-click `funding-service` folder → Deploy to Web App
3. Create new app or select existing
4. Configure environment variables in portal

### Step 3: Deploy Other Services

Repeat the same process for:
- **Wallet Service**: `2aside-wallet.azurewebsites.net`
- **User Service**: `2aside-user.azurewebsites.net`
- **Admin Service**: `2aside-admin.azurewebsites.net`

Or combine all services into one App Service for simplicity during beta.

---

## Part 4: Frontend Deployment (Vercel - Recommended)

### Why Vercel?
- Free SSL certificate
- Automatic deployments from GitHub
- Works perfectly on mobile
- Instant preview URLs for testing
- Zero configuration for Next.js

### Step 1: Prepare Frontend

1. **Update API endpoints in `.env.production`**:

Create `2aside-frontend/.env.production`:

```env
NEXT_PUBLIC_API_URL=https://2aside-api.azurewebsites.net
NEXT_PUBLIC_USER_SERVICE_URL=https://2aside-user.azurewebsites.net
NEXT_PUBLIC_WALLET_SERVICE_URL=https://2aside-wallet.azurewebsites.net
NEXT_PUBLIC_FUNDING_SERVICE_URL=https://2aside-api.azurewebsites.net
NEXT_PUBLIC_ADMIN_SERVICE_URL=https://2aside-admin.azurewebsites.net
```

### Step 2: Deploy to Vercel

1. **Sign up at**: https://vercel.com (free for hobby projects)

2. **Import your repository**:
   - Click "New Project"
   - Import from GitHub (authorize Vercel)
   - Select `2aside-frontend` directory
   - Framework preset: Next.js (auto-detected)

3. **Configure build settings**:
   - Root Directory: `2aside-frontend`
   - Build Command: `npm run build` (default)
   - Output Directory: `.next` (default)

4. **Add environment variables** (in Vercel dashboard):
   - Copy all variables from `.env.production`
   - Click "Deploy"

5. **Your app is live!**
   - URL: `https://2aside-[random].vercel.app`
   - Custom domain: Add your own domain later (free)

### Step 3: Enable Mobile PWA Features (Optional)

Add to `2aside-frontend/public/manifest.json`:

```json
{
  "name": "2-Aside Platform",
  "short_name": "2-Aside",
  "description": "Peer-to-peer funding platform",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

This allows users to "install" the app on their phone's home screen.

---

## Part 5: Update Backend CORS

After frontend is deployed, update CORS in all backend services:

```python
allow_origins=[
    "http://localhost:3000",
    "https://2aside-[random].vercel.app",  # Your Vercel URL
    "https://your-custom-domain.com",      # If you add custom domain
]
```

Redeploy backend services.

---

## Part 6: Testing with Beta Users

### Share These URLs:

1. **Web App**: `https://2aside-[random].vercel.app`
   - Works on any browser (desktop, mobile, tablet)
   - Fully responsive

2. **Mobile Testing**:
   - Send link via WhatsApp/SMS
   - Opens in mobile browser
   - Users can add to home screen (PWA)

### Progressive Updates Workflow:

1. **Make code changes locally**
2. **Test locally**: `npm run dev` or `python -m uvicorn main:app`
3. **Push to GitHub**: `git push origin main`
4. **Vercel auto-deploys** (30-60 seconds)
5. **Azure App Service auto-deploys** (2-3 minutes)
6. **Beta testers get updates** automatically on next page refresh

### Preview Deployments (Vercel Feature):

- Every git branch gets its own preview URL
- Test features before merging to main
- Example: `https://2aside-git-feature-branch.vercel.app`

---

## Part 7: Monitoring & Logs

### Backend Logs (Azure):
1. Go to App Service → Log stream
2. See real-time logs
3. Diagnose issues

### Frontend Logs (Vercel):
1. Vercel dashboard → Your project → Deployments
2. Click deployment → View logs
3. See build and runtime logs

### Database Monitoring (Azure SQL):
1. Azure Portal → SQL Database → Metrics
2. Monitor DTU usage, connections, etc.

---

## Cost Breakdown (Monthly)

### Beta/Testing Phase:
- **Azure Blob Storage**: $1-2/month (few GB)
- **Azure SQL Database Basic**: $5/month
- **Azure App Service Basic B1**: $13/month (×4 services = $52) or Free tier
- **Vercel**: FREE (hobby tier)
- **Total**: ~$20-60/month

### Production (Scaled):
- **Azure Blob Storage**: $5-10/month
- **Azure SQL Database Standard**: $30-100/month
- **Azure App Service Standard**: $75/month
- **Vercel Pro**: $20/month (optional, for team features)
- **Total**: ~$150-250/month

---

## Alternative: All-in-One Azure Deployment

If you prefer everything on Azure:

1. **Frontend**: Azure Static Web Apps (free tier)
2. **Backend**: Azure App Service
3. **Database**: Azure SQL Database
4. **Storage**: Azure Blob Storage

**Benefits**:
- Everything in one ecosystem
- Easier security/networking setup
- Single billing

**Steps**:
1. Deploy frontend to Azure Static Web Apps (similar to Vercel)
2. Link to GitHub for auto-deployment
3. Configure API routes to backend App Service

---

## Mobile App Considerations

### Current Setup (Web App):
- Responsive design ✅
- Works on all devices ✅
- Can be added to home screen (PWA) ✅
- No app store needed ✅

### Future Native App (if needed):
- Use React Native (reuse React components)
- Same backend API
- Publish to Google Play / App Store
- **Cost**: $25 (Google) + $99/year (Apple) + development time

**Recommendation**: Start with web app (PWA) for beta testing, consider native app later if needed.

---

## Next Steps

1. ✅ **Set up Azure Blob Storage** (follow Part 1)
2. ✅ **Test locally with Azure storage**
3. ⬜ **Create Azure App Service** for backend
4. ⬜ **Deploy backend services** to Azure
5. ⬜ **Deploy frontend** to Vercel
6. ⬜ **Update CORS** with production URLs
7. ⬜ **Test end-to-end** on mobile device
8. ⬜ **Share with beta testers**

---

## Quick Start Commands

### Local Development:
```bash
# Backend
cd 2-Aside/funding-service
python -m uvicorn main:app --reload

# Frontend
cd 2aside-frontend
npm run dev
```

### Deploy Frontend:
```bash
cd 2aside-frontend
git add .
git commit -m "Update feature"
git push origin main
# Vercel auto-deploys
```

### Deploy Backend:
```bash
cd 2-Aside/funding-service
git add .
git commit -m "Update API"
git push origin main
# Azure auto-deploys
```

---

## Support Resources

- **Azure Documentation**: https://docs.microsoft.com/azure
- **Vercel Documentation**: https://vercel.com/docs
- **Next.js Deployment**: https://nextjs.org/docs/deployment
- **FastAPI Deployment**: https://fastapi.tiangolo.com/deployment/

---

## Security Checklist for Production

- [ ] Change all default passwords
- [ ] Use environment variables for secrets (never commit)
- [ ] Enable HTTPS only (auto with Vercel/Azure)
- [ ] Rotate database credentials
- [ ] Enable Azure SQL firewall rules
- [ ] Set up API rate limiting
- [ ] Enable Azure DDoS protection
- [ ] Regular security updates (pip, npm)
- [ ] Monitor logs for suspicious activity
- [ ] Backup database regularly
