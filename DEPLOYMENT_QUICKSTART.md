# Azure Container Apps - Quick Start Guide

## 🚀 Fast Track to Production (30-60 minutes)

Follow these steps to get your 2-Aside platform live for beta testing.

---

## ✅ Prerequisites Checklist

- [ ] Azure account ([Sign up free](https://azure.com))
- [ ] GitHub account
- [ ] Code pushed to GitHub
- [ ] Azure Blob Storage configured (see [AZURE_SETUP_INSTRUCTIONS.md](2-Aside/AZURE_SETUP_INSTRUCTIONS.md))
- [ ] Database accessible from internet

---

## 📋 Step-by-Step Deployment

### **Step 1: Create Azure Resources (10 minutes)**

1. **Login to** [Azure Portal](https://portal.azure.com)

2. **Create Resource Group**:
   - Search "Resource groups" → Create
   - Name: `2aside-resources`
   - Region: "South Africa North" or "West Europe"

3. **Create Container Registry**:
   - Search "Container registries" → Create
   - Name: `2asideregistry` (must be unique)
   - SKU: Basic ($5/month)
   - Enable "Admin user" in Access keys

4. **Save these values** (you'll need them):
   - Registry login server: `2asideregistry.azurecr.io`
   - Username: (from Access keys)
   - Password: (from Access keys)

---

### **Step 2: Set Up GitHub Secrets (5 minutes)**

Go to GitHub → Your Repo → Settings → Secrets → Actions → New secret

Add these secrets:

| Secret Name | Where to Get Value |
|------------|-------------------|
| `REGISTRY_LOGIN_SERVER` | `2asideregistry.azurecr.io` |
| `REGISTRY_USERNAME` | Azure Portal → Container Registry → Access keys |
| `REGISTRY_PASSWORD` | Azure Portal → Container Registry → Access keys (password) |
| `DATABASE_URL` | Your SQL Server connection string |
| `JWT_SECRET` | Generate: `openssl rand -base64 32` |
| `AZURE_STORAGE_CONNECTION_STRING` | From Azure Blob Storage setup |

---

### **Step 3: Get Azure Credentials (5 minutes)**

1. **Azure Portal** → Click cloud shell icon (>_)
2. **Run this command** (replace `{subscription-id}` with yours):

```bash
az ad sp create-for-rbac \
  --name "2aside-github-deploy" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/2aside-resources \
  --sdk-auth
```

3. **Copy entire JSON output**
4. **Add as GitHub secret**: `AZURE_CREDENTIALS`

**Find your subscription ID**: Azure Portal → Subscriptions

---

### **Step 4: Create GitHub Actions Workflows (10 minutes)**

Create these 3 files in your repo:

#### **`.github/workflows/deploy-user-service.yml`**

```yaml
name: Deploy User Service

on:
  push:
    branches: [ main ]
    paths:
      - '2-Aside/user-service/**'
      - '2-Aside/shared/**'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Login to ACR
      uses: docker/login-action@v2
      with:
        registry: ${{ secrets.REGISTRY_LOGIN_SERVER }}
        username: ${{ secrets.REGISTRY_USERNAME }}
        password: ${{ secrets.REGISTRY_PASSWORD }}

    - name: Build and push
      working-directory: ./2-Aside
      run: |
        docker build -f user-service/Dockerfile \
          -t ${{ secrets.REGISTRY_LOGIN_SERVER }}/user-service:latest .
        docker push ${{ secrets.REGISTRY_LOGIN_SERVER }}/user-service:latest

    - name: Login to Azure
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Deploy to Container Apps
      uses: azure/container-apps-deploy-action@v1
      with:
        containerAppName: 2aside-user-service
        resourceGroup: 2aside-resources
        imageToDeploy: ${{ secrets.REGISTRY_LOGIN_SERVER }}/user-service:latest
```

#### **Create similar files for**:
- `deploy-wallet-service.yml` (change "user" to "wallet")
- `deploy-funding-service.yml` (change "user" to "funding")

---

### **Step 5: Push to GitHub (1 minute)**

```bash
git add .
git commit -m "Add Azure Container Apps deployment"
git push origin main
```

**GitHub Actions will start automatically!**

Monitor: GitHub Repo → Actions tab

---

### **Step 6: Configure Container Apps (10 minutes)**

After GitHub Actions completes (first run takes ~10-15 min):

For **each** Container App (user-service, wallet-service, funding-service):

1. **Azure Portal** → Search "Container Apps"
2. **Click your app** (e.g., "2aside-user-service")
3. **Go to "Secrets"** → Add:
   - `database-url`: Your DATABASE_URL
   - `jwt-secret`: Your JWT_SECRET
4. **Go to "Ingress"**:
   - Enable: Yes
   - Traffic: Anywhere
   - Type: HTTP
   - Port: 8000
   - Save
5. **Copy the URL** (looks like: `https://2aside-user-service.xxx.azurecontainerapps.io`)

---

### **Step 7: Deploy Frontend to Vercel (10 minutes)**

1. **Update frontend env**: Create `2aside-frontend/.env.production`

```env
NEXT_PUBLIC_USER_SERVICE_URL=https://2aside-user-service.xxx.azurecontainerapps.io
NEXT_PUBLIC_WALLET_SERVICE_URL=https://2aside-wallet-service.xxx.azurecontainerapps.io
NEXT_PUBLIC_API_URL=https://2aside-funding-service.xxx.azurecontainerapps.io
NEXT_PUBLIC_FUNDING_SERVICE_URL=https://2aside-funding-service.xxx.azurecontainerapps.io
```

2. **Go to** [vercel.com](https://vercel.com) → Sign in with GitHub
3. **Import project** → Select your repo
4. **Configure**:
   - Root Directory: `2aside-frontend`
   - Framework: Next.js (auto-detected)
5. **Add environment variables** (copy from .env.production)
6. **Deploy** → Wait ~2 minutes
7. **Copy Vercel URL**: `https://2aside-xxx.vercel.app`

---

### **Step 8: Update Backend CORS (5 minutes)**

Update all 3 backend services' `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://2aside-xxx.vercel.app",  # Your Vercel URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Push changes**:
```bash
git add .
git commit -m "Update CORS for production"
git push origin main
```

---

## 🎉 You're Live!

**Share with beta testers**: `https://2aside-xxx.vercel.app`

**Works on**:
- Desktop browsers
- Mobile browsers (iOS/Android)
- Tablets

---

## 📱 Test on Mobile

1. **Open Safari/Chrome on phone**
2. **Go to** your Vercel URL
3. **Add to home screen** (iOS: Share → Add to Home Screen)
4. **App opens full screen** like native app

---

## 🔄 Progressive Updates

**Every time you push code**:

1. **GitHub Actions** auto-builds Docker images (2-3 min)
2. **Azure Container Apps** auto-deploys backend (1-2 min)
3. **Vercel** auto-deploys frontend (30 sec)
4. **Users get updates** on next page refresh

**No downtime!** Azure uses rolling deployments.

---

## 💰 Cost Estimate

**Beta testing** (~100 users, light usage):
- **~$20-30/month total**

**What you're paying for**:
- Azure Container Registry: $5/month
- Azure Container Apps: $10-20/month (3 services)
- Azure Blob Storage: $1/month
- Azure SQL Database: $5/month (Basic tier)
- Vercel: FREE

---

## 🐛 Troubleshooting

### Container won't start?
- Check logs: Azure Portal → Container App → Log stream
- Verify secrets are set correctly

### Can't access service?
- Check Ingress is enabled
- Verify port is 8000
- Test health endpoint: `https://your-app-url/health`

### Frontend can't connect to backend?
- Check CORS includes Vercel URL
- Verify environment variables in Vercel
- Check browser console for errors

### Database connection fails?
- Allow Azure services in SQL Server firewall
- Test connection string format
- Check connection from Azure Cloud Shell

---

## 📊 Monitor Your App

**View Logs**:
- Azure Portal → Container App → Log stream

**View Metrics**:
- Azure Portal → Container App → Metrics
- See: Requests, CPU, Memory

**Set Up Alerts**:
- Azure Portal → Container App → Alerts
- Example: Email when errors > 10

---

## 🔐 Security Checklist

- [ ] Change JWT_SECRET to random 32+ character string
- [ ] Use strong database password
- [ ] Enable Azure SQL firewall (allow only Azure services)
- [ ] Don't commit `.env` files to Git
- [ ] Rotate secrets periodically
- [ ] Enable HTTPS only (automatic)

---

## 📞 Need Help?

**Full Documentation**: [AZURE_CONTAINER_APPS_DEPLOYMENT.md](AZURE_CONTAINER_APPS_DEPLOYMENT.md)

**Azure Support**: https://portal.azure.com → Support

**GitHub Actions Logs**: Your Repo → Actions → Click failed workflow

**Common Issues**: Check [AZURE_CONTAINER_APPS_DEPLOYMENT.md](AZURE_CONTAINER_APPS_DEPLOYMENT.md) → Troubleshooting section

---

## ✅ Success Checklist

- [ ] All GitHub Actions workflows passed (green checkmarks)
- [ ] All 3 Container Apps show "Running" status
- [ ] Health endpoints return {"status": "ok"}
- [ ] Frontend loads on Vercel
- [ ] Can register/login from mobile phone
- [ ] Can create funding request
- [ ] Can upload payment proof
- [ ] No CORS errors in browser console

---

## 🚀 Next Steps

1. **Share with beta testers** via WhatsApp/Email
2. **Monitor usage** in Azure Portal
3. **Collect feedback** from users
4. **Make updates** → Push to GitHub → Auto-deploys!
5. **Scale up** as needed (Azure auto-scales)

**Welcome to production!** 🎊
