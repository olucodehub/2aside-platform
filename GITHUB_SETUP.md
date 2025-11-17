# GitHub Repository Setup Guide

## Step-by-Step Instructions to Push to New Repository

### Step 1: Initialize Git Repository (if not already done)

Open PowerShell in `C:\Dev\Rendezvous`:

```powershell
cd C:\Dev\Rendezvous

# Check if git is already initialized
git status

# If not initialized, run:
git init
```

### Step 2: Add Your GitHub Repository as Remote

Replace `YOUR_GITHUB_USERNAME` and `REPO_NAME` with your actual values:

```powershell
# Remove old remote if exists
git remote remove origin

# Add new remote
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/2aside-platform.git

# Verify remote
git remote -v
```

**Example:**
```powershell
git remote add origin https://github.com/johndoe/2aside-platform.git
```

### Step 3: Check What Will Be Committed

```powershell
# See what files will be added
git status

# Make sure .env files are NOT listed (should be ignored)
# If you see .env files, they're being ignored correctly
```

**Important files that SHOULD be committed:**
- ✅ All `.py` files
- ✅ All `.tsx`, `.ts`, `.jsx`, `.js` files
- ✅ `Dockerfile`, `docker-compose.yml`
- ✅ `requirements.txt`, `package.json`
- ✅ `.md` documentation files
- ✅ `.gitignore`, `README.md`

**Files that should NOT be committed (should be in .gitignore):**
- ❌ `.env`, `.env.local`, `.env.production`
- ❌ `node_modules/`, `__pycache__/`
- ❌ `venv/`, `.venv/`
- ❌ Database files (`.db`, `.sqlite`)
- ❌ `uploads/` folder

### Step 4: Stage All Files

```powershell
# Add all files
git add .

# Check status again
git status
```

### Step 5: Commit Changes

```powershell
git commit -m "Initial commit: 2-Aside P2P funding platform

- Python microservices (user, wallet, funding)
- Next.js frontend with TypeScript
- Azure Blob Storage integration
- Docker & Azure Container Apps ready
- Comprehensive deployment documentation"
```

### Step 6: Create Main Branch and Push

```powershell
# Rename branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

**If this is your first time pushing:**
You may be prompted to login to GitHub. Follow the authentication prompts.

### Step 7: Verify on GitHub

1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/2aside-platform`
2. You should see all your files
3. Check that README.md displays correctly
4. Verify `.env` files are NOT visible (they should be ignored)

---

## Common Issues & Solutions

### Issue: "Support for password authentication was removed"

**Solution:** Use Personal Access Token

1. **GitHub** → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. **Generate new token** → Select scopes: `repo` (all)
3. **Copy token** (you won't see it again!)
4. **When pushing, use token as password**:
   ```
   Username: your_github_username
   Password: ghp_yourPersonalAccessToken
   ```

**Or configure Git to use token:**
```powershell
git remote set-url origin https://YOUR_TOKEN@github.com/YOUR_USERNAME/2aside-platform.git
```

### Issue: ".env file is in repository"

**Solution:** Remove it and add to .gitignore

```powershell
# Remove from git tracking (but keep local file)
git rm --cached .env
git rm --cached 2-Aside/.env
git rm --cached 2aside-frontend/.env.local

# Commit the removal
git commit -m "Remove environment files from tracking"
git push
```

### Issue: "Too many files to commit"

The `.gitignore` file should handle this, but if you see old `.NET` or `React` files:

```powershell
# Remove old folders from tracking
git rm -r --cached RendezvousFrontEnd
git rm -r --cached Rendezvous/Api
git rm -r --cached Rendezvous/BLL
git rm -r --cached Rendezvous/DAL

git commit -m "Remove old .NET architecture files"
```

### Issue: "node_modules or venv is being committed"

```powershell
# Remove from tracking
git rm -r --cached node_modules
git rm -r --cached venv
git rm -r --cached 2-Aside/venv

git commit -m "Remove dependency folders from tracking"
git push
```

---

## Next Steps After Pushing

### 1. Create .env.example Templates

For security, create example files without actual secrets:

**2-Aside/.env.example:**
```env
DATABASE_URL=mssql+pyodbc://username:password@server:1433/database?driver=ODBC+Driver+18+for+SQL+Server
JWT_SECRET=your-secret-key-min-32-characters
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER_NAME=payment-proofs
```

**2aside-frontend/.env.example:**
```env
NEXT_PUBLIC_USER_SERVICE_URL=http://localhost:8001
NEXT_PUBLIC_WALLET_SERVICE_URL=http://localhost:8002
NEXT_PUBLIC_FUNDING_SERVICE_URL=http://localhost:8003
```

**Commit these:**
```powershell
git add 2-Aside/.env.example 2aside-frontend/.env.example
git commit -m "Add environment variable templates"
git push
```

### 2. Set Up GitHub Secrets

Now follow **DEPLOYMENT_QUICKSTART.md** → **Step 2: Set Up GitHub Secrets**

Go to your repo: Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
- `REGISTRY_LOGIN_SERVER`
- `REGISTRY_USERNAME`
- `REGISTRY_PASSWORD`
- `AZURE_CREDENTIALS`
- `DATABASE_URL`
- `JWT_SECRET`
- `AZURE_STORAGE_CONNECTION_STRING`

### 3. Create GitHub Actions Workflows

Create `.github/workflows/` directory and add deployment workflows.

See **DEPLOYMENT_QUICKSTART.md** Step 4 for workflow templates.

---

## Branch Strategy

### For Beta Testing:
```
main (production)
  ↓
  Always deploy to Azure from this branch
```

### For Development:
```
main (production)
  ↑
develop (testing)
  ↑
feature/new-feature (your work)
```

**Recommended workflow:**
1. Create feature branch: `git checkout -b feature/payment-notifications`
2. Make changes and commit
3. Push feature branch: `git push -u origin feature/payment-notifications`
4. Create Pull Request on GitHub
5. Review and merge to main
6. GitHub Actions auto-deploys to Azure

---

## Useful Git Commands

```powershell
# Check current status
git status

# See commit history
git log --oneline

# Create new branch
git checkout -b feature/new-feature

# Switch branches
git checkout main

# Pull latest changes
git pull origin main

# See differences
git diff

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard local changes
git checkout -- filename
```

---

## Repository Settings Recommendations

### 1. Branch Protection (Optional but recommended)

GitHub → Your Repo → Settings → Branches → Add rule

For `main` branch:
- ✅ Require pull request before merging
- ✅ Require status checks to pass (after setting up GitHub Actions)
- ✅ Require conversation resolution before merging

### 2. Enable Issues

GitHub → Your Repo → Settings → Features:
- ✅ Issues (for tracking bugs/features)

### 3. Add Collaborators (if needed)

Settings → Collaborators → Add people

---

## What to Do After First Push

1. ✅ **Verify repository** on GitHub
2. ✅ **Check .gitignore** worked (no .env files visible)
3. ✅ **Read README** displays correctly
4. ✅ **Set up GitHub Secrets** (for deployment)
5. ✅ **Create GitHub Actions workflows**
6. ✅ **Test deployment** to Azure Container Apps

---

## Quick Reference

**Repository URL:** `https://github.com/YOUR_USERNAME/2aside-platform`

**Clone command:**
```bash
git clone https://github.com/YOUR_USERNAME/2aside-platform.git
```

**Update local repo:**
```bash
git pull origin main
```

**Push changes:**
```bash
git add .
git commit -m "Your message"
git push origin main
```

---

## Success Checklist

- [ ] Created new GitHub repository
- [ ] Added remote origin
- [ ] Committed all code
- [ ] Pushed to main branch
- [ ] Verified on GitHub (no .env files visible)
- [ ] Created .env.example files
- [ ] Set up GitHub Secrets
- [ ] Ready for deployment!

**Next:** Follow [DEPLOYMENT_QUICKSTART.md](DEPLOYMENT_QUICKSTART.md) to deploy to Azure Container Apps!
