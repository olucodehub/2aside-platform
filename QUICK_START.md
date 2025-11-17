# 2-Aside Quick Start Guide

## 🚀 Starting the Application

### Option 1: Use the PowerShell Script (Recommended)
```powershell
cd C:\Dev\Rendezvous
.\start-all-services.ps1
```

### Option 2: Double-Click
1. Navigate to `C:\Dev\Rendezvous\`
2. Right-click `start-all-services.ps1`
3. Select **"Run with PowerShell"**

---

## 🛑 Stopping the Application

```powershell
cd C:\Dev\Rendezvous
.\stop-all-services.ps1
```

Or just close all the PowerShell windows.

---

## 📊 Check Status

```powershell
cd C:\Dev\Rendezvous
.\check-services-status.ps1
```

This will show you:
- Which services are running
- Health status of each service
- Next merge cycle time
- Whether join window is open

---

## 🌐 Service URLs

| Service | URL | Documentation |
|---------|-----|---------------|
| **Frontend** | http://localhost:3000 | - |
| **API Gateway** | http://localhost:8000 | http://localhost:8000/docs |
| **Auth Service** | http://localhost:8001 | http://localhost:8001/docs |
| **Wallet Service** | http://localhost:8002 | http://localhost:8002/docs |
| **User Service** | http://localhost:8003 | http://localhost:8003/docs |
| **Funding Service** | http://localhost:8004 | http://localhost:8004/docs |

---

## ⏰ Merge Cycle Times

**Automatic matching runs at:**
- **9:00 AM WAT** (West Africa Time)
- **3:00 PM WAT**
- **9:00 PM WAT**

**Join Window:**
- Opens exactly at merge time
- Lasts for 5 minutes
- Users must click "Join Merge Cycle" during this window

---

## ✅ What's Included

✓ **6 Services** - All backend services + frontend
✓ **Auto-Matching** - Built into Funding Service
✓ **No Celery** - No longer needed!
✓ **No Redis** - No longer needed!
✓ **Hot Reload** - Code changes auto-restart services

---

## 🔧 Troubleshooting

### Execution Policy Error
```powershell
powershell -ExecutionPolicy Bypass -File start-all-services.ps1
```

### Port Already in Use
```powershell
.\stop-all-services.ps1
.\start-all-services.ps1
```

### Service Won't Connect to Database
Check your `.env` files in each service folder for correct Azure SQL connection strings.

### Auto-Matching Not Working
Check the Funding Service window for:
```
✓ Auto-matching scheduler started
✓ Matching will run automatically at 9am, 3pm, 9pm WAT
```

---

## 📚 Documentation

- **Startup Scripts**: [STARTUP_SCRIPTS_README.md](STARTUP_SCRIPTS_README.md)
- **Merge Cycle System**: [2-Aside/MERGE_CYCLE_SIMPLIFICATION.md](2-Aside/MERGE_CYCLE_SIMPLIFICATION.md)
- **API Docs**: Visit any service's `/docs` endpoint

---

## 🎯 Common Tasks

### Create a Funding Request
```bash
curl -X POST "http://localhost:8004/funding/request?amount=5000&currency=NAIRA" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Check Next Merge Time
```bash
curl http://localhost:8004/merge-cycle/next
```

### Join Merge Cycle (during 5-min window)
```bash
curl -X POST http://localhost:8004/merge-cycle/join \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 💡 Tips

1. **Check Status First**: Run `check-services-status.ps1` to see what's running
2. **Use Separate Windows**: Each service runs in its own window so you can see logs
3. **Hot Reload**: Backend changes auto-restart (uvicorn `--reload` flag)
4. **Frontend Hot Reload**: Next.js automatically updates on file changes
5. **API Testing**: Use Swagger UI at `http://localhost:PORT/docs`

---

## 🆘 Need Help?

1. Check service logs in the PowerShell windows
2. Run `check-services-status.ps1` to diagnose issues
3. Review documentation files in this folder
4. Check Azure Portal for database connectivity

---

**Ready to start? Run:**
```powershell
.\start-all-services.ps1
```

**Then open:** http://localhost:3000
