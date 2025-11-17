# 2-Aside Application Startup Scripts

This folder contains PowerShell scripts to easily start and stop all services for the 2-Aside application.

## Scripts

### 1. `start-all-services.ps1`
Starts all backend services and frontend in separate PowerShell windows.

### 2. `stop-all-services.ps1`
Stops all running services (kills processes on ports 8000-8004 and 3000).

---

## How to Use

### Starting All Services

**Option 1: Double-click the script**
1. Navigate to `C:\Dev\Rendezvous\`
2. Right-click `start-all-services.ps1`
3. Select **"Run with PowerShell"**

**Option 2: Run from PowerShell**
```powershell
cd C:\Dev\Rendezvous
.\start-all-services.ps1
```

**Option 3: Run from Command Prompt**
```cmd
cd C:\Dev\Rendezvous
powershell -ExecutionPolicy Bypass -File start-all-services.ps1
```

### Stopping All Services

**Option 1: Double-click the script**
1. Navigate to `C:\Dev\Rendezvous\`
2. Right-click `stop-all-services.ps1`
3. Select **"Run with PowerShell"**

**Option 2: Run from PowerShell**
```powershell
cd C:\Dev\Rendezvous
.\stop-all-services.ps1
```

**Option 3: Run from Command Prompt**
```cmd
cd C:\Dev\Rendezvous
powershell -ExecutionPolicy Bypass -File stop-all-services.ps1
```

---

## Execution Policy Issues

If you get an error like:
```
start-all-services.ps1 cannot be loaded because running scripts is disabled on this system
```

### Solution 1: Run with Bypass (Temporary)
```powershell
powershell -ExecutionPolicy Bypass -File start-all-services.ps1
```

### Solution 2: Change Execution Policy (Permanent)
Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then you can run the scripts normally.

---

## What Gets Started

When you run `start-all-services.ps1`, the following services start:

| Service | Port | URL |
|---------|------|-----|
| API Gateway | 8000 | http://localhost:8000 |
| Auth Service | 8001 | http://localhost:8001 |
| Wallet Service | 8002 | http://localhost:8002 |
| User Service | 8003 | http://localhost:8003 |
| Funding Service | 8004 | http://localhost:8004 |
| Frontend | 3000 | http://localhost:3000 |

### API Documentation
Each backend service has Swagger docs:
- API Gateway: http://localhost:8000/docs
- Auth Service: http://localhost:8001/docs
- Wallet Service: http://localhost:8002/docs
- User Service: http://localhost:8003/docs
- Funding Service: http://localhost:8004/docs

---

## What You DON'T Need Anymore

The following are **NO LONGER NEEDED** after the merge cycle simplification:

❌ **Celery Worker** - Removed
❌ **Celery Beat** - Removed
❌ **Redis** - Removed

**Auto-matching now runs automatically inside the Funding Service at 9am, 3pm, and 9pm WAT!**

---

## Verifying Services Are Running

### Check Backend Health
```powershell
curl http://localhost:8000/health  # API Gateway
curl http://localhost:8001/health  # Auth Service
curl http://localhost:8002/health  # Wallet Service
curl http://localhost:8003/health  # User Service
curl http://localhost:8004/health  # Funding Service
```

### Check Merge Cycle Scheduler
```powershell
curl http://localhost:8004/merge-cycle/next
```

Should return JSON with next merge time at 9am, 3pm, or 9pm WAT.

### Check Frontend
Open browser: http://localhost:3000

---

## Troubleshooting

### Service Won't Start
1. Check if port is already in use:
   ```powershell
   netstat -ano | findstr :8000  # Replace 8000 with the port number
   ```

2. Run the stop script first:
   ```powershell
   .\stop-all-services.ps1
   ```

3. Try starting again:
   ```powershell
   .\start-all-services.ps1
   ```

### Database Connection Issues
- Ensure your Azure SQL Server is running
- Check `.env` files in each service folder for correct connection strings
- Verify firewall rules allow your IP address

### Frontend Won't Start
- Make sure Node.js is installed: `node --version`
- Make sure dependencies are installed:
  ```powershell
  cd C:\Dev\Rendezvous\2aside-frontend
  npm install
  ```

### Auto-Matching Not Working
Check the Funding Service window for startup messages:
```
✓ Auto-matching scheduler started
✓ Matching will run automatically at 9am, 3pm, 9pm WAT
```

If you don't see these messages, check the logs for errors.

---

## Manual Service Management

If you prefer to start services individually:

### Start API Gateway
```powershell
cd C:\Dev\Rendezvous\2-Aside\api-gateway
uvicorn main:app --reload --port 8000
```

### Start Auth Service
```powershell
cd C:\Dev\Rendezvous\2-Aside\auth-service
uvicorn main:app --reload --port 8001
```

### Start Wallet Service
```powershell
cd C:\Dev\Rendezvous\2-Aside\wallet-service
uvicorn main:app --reload --port 8002
```

### Start User Service
```powershell
cd C:\Dev\Rendezvous\2-Aside\user-service
uvicorn main:app --reload --port 8003
```

### Start Funding Service
```powershell
cd C:\Dev\Rendezvous\2-Aside\funding-service
uvicorn main:app --reload --port 8004
```

### Start Frontend
```powershell
cd C:\Dev\Rendezvous\2aside-frontend
npm run dev
```

---

## Development Tips

### Hot Reload
All backend services use `--reload` flag, so code changes automatically restart the service.

Frontend uses Next.js dev server with hot module replacement.

### Viewing Logs
Each service runs in its own PowerShell window, so you can see real-time logs for each service separately.

### Stopping Individual Services
Just close the PowerShell window for that service, or press `Ctrl+C` in the window.

---

## Support

For issues with:
- **Merge Cycle System**: See [MERGE_CYCLE_SIMPLIFICATION.md](C:\Dev\Rendezvous\2-Aside\MERGE_CYCLE_SIMPLIFICATION.md)
- **General Setup**: Check service-specific README files
- **Scripts**: Verify paths in the PowerShell scripts match your directory structure
