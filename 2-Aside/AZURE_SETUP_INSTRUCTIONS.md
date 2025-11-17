# Azure Blob Storage Setup Instructions

## Step 1: Install Azure SDK

Run this in the funding-service directory:

```bash
pip install azure-storage-blob azure-identity python-dotenv
```

## Step 2: Create Azure Storage Account

1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource"
3. Search for "Storage account" and click Create
4. Fill in the details:
   - **Resource Group**: Create new or use existing
   - **Storage account name**: Choose a unique name (e.g., `2aside-storage`)
   - **Region**: Choose closest to your users (e.g., `West US`, `West Europe`)
   - **Performance**: Standard
   - **Redundancy**: LRS (Locally Redundant Storage) for dev, GRS for production
5. Click "Review + Create" then "Create"

## Step 3: Get Connection String

1. Once deployed, go to your Storage Account
2. In the left menu, click "Access keys" under "Security + networking"
3. Click "Show" next to "Connection string" for key1
4. Copy the entire connection string (starts with `DefaultEndpointsProtocol=https...`)

## Step 4: Configure Environment Variables

1. Navigate to `2-Aside/funding-service/` directory
2. Create a `.env` file (copy from `.env.example`)
3. Paste your connection string:

```env
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=2asidestoragetest;AccountKey=YOUR_KEY_HERE;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=payment-proofs
```

## Step 5: Container Creation

The container named "payment-proofs" will be created automatically when the service starts.

Alternatively, you can create it manually:
1. Go to your Storage Account in Azure Portal
2. Click "Containers" in the left menu
3. Click "+ Container"
4. Name: `payment-proofs`
5. Public access level: **Private** (recommended)
6. Click "Create"

## Step 6: Optional - Configure CORS (if needed)

If you need to access blobs directly from browser:

1. In Storage Account, go to "Resource sharing (CORS)"
2. Click "Blob service"
3. Add a rule:
   - Allowed origins: `http://localhost:3000` (add production URL later)
   - Allowed methods: GET, POST, PUT
   - Allowed headers: `*`
   - Exposed headers: `*`
   - Max age: 3600
4. Click "Save"

## Step 7: Load Environment Variables

Update the funding service to load environment variables. In `main.py`, add at the top:

```python
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file
```

## Step 8: Restart Service

Restart the funding service. You should see in the console:

```
[OK] Using existing blob container: payment-proofs
[OK] Blob cleanup scheduler started
```

## Step 9: Test Upload

1. Create a match between two users
2. Upload a payment proof image
3. Check Azure Portal → Your Storage Account → Containers → payment-proofs
4. You should see the uploaded file

## Step 10: Test Cleanup

To test the 7-day deletion:

1. Upload a proof and confirm payment
2. Check the blob metadata in Azure Portal (should have `delete_after` metadata)
3. Wait for the cleanup task to run (midnight daily)
4. Or manually trigger cleanup by calling the function

## Monitoring Costs

1. Go to Storage Account → Cost analysis
2. View current month spending
3. Typical costs for this use case: <$1/month for small scale

## Security Best Practices

### For Development:
- Use separate storage accounts for dev/staging/prod
- Rotate access keys periodically

### For Production:
- Enable "Soft delete" for blobs (allows recovery)
- Enable versioning
- Use Managed Identity instead of connection strings
- Set up diagnostic logging
- Configure firewall rules to restrict access

## Fallback Behavior

The system is designed with fallback:
- If Azure is not configured, files are saved locally to `uploads/payment_proofs/`
- No errors will occur, but you'll see a warning in logs
- This allows development without Azure setup

## Troubleshooting

### "Azure Blob Storage not configured" warning
- Check that `.env` file exists in `funding-service/` directory
- Verify connection string is correct
- Ensure python-dotenv is installed

### Connection errors
- Check your internet connection
- Verify Azure Storage Account is running
- Check firewall settings

### Files not deleting after 7 days
- Check that cleanup scheduler started: Look for log message
- Verify blob has `delete_after` metadata set
- Check Azure Portal logs for errors
