# Azure Blob Storage Implementation Guide

## Overview
This document outlines the steps to implement Azure Blob Storage for payment proof uploads with automatic deletion after 7 days from confirmation.

## Backend Changes (Python/FastAPI)

### 1. Install Azure SDK
```bash
pip install azure-storage-blob azure-identity python-dotenv
```

### 2. Environment Variables (.env file)
```
AZURE_STORAGE_CONNECTION_STRING=your_connection_string_here
AZURE_STORAGE_CONTAINER_NAME=payment-proofs
```

### 3. Azure Blob Service (create new file: `2-Aside/funding-service/azure_blob_service.py`)
```python
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
import os
import uuid
from pathlib import Path

class AzureBlobService:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "payment-proofs")
        self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)

        # Ensure container exists
        try:
            self.container_client = self.blob_service_client.get_container_client(self.container_name)
            if not self.container_client.exists():
                self.container_client.create_container()
        except Exception as e:
            print(f"Error creating container: {e}")

    def upload_file(self, file_content, filename: str, content_type: str = "image/jpeg") -> str:
        """
        Upload file to Azure Blob Storage
        Returns the blob URL
        """
        # Generate unique blob name
        file_ext = Path(filename).suffix
        blob_name = f"{uuid.uuid4()}{file_ext}"

        # Upload blob
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )

        blob_client.upload_blob(
            file_content,
            content_settings={
                'content_type': content_type
            },
            overwrite=True
        )

        # Return the blob URL
        return blob_client.url

    def delete_blob(self, blob_url: str):
        """Delete a blob from storage"""
        try:
            # Extract blob name from URL
            blob_name = blob_url.split(f"{self.container_name}/")[-1]
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            return True
        except Exception as e:
            print(f"Error deleting blob: {e}")
            return False

    def schedule_deletion(self, blob_url: str, days: int = 7):
        """
        Set blob metadata with deletion date
        A background task will clean up expired blobs
        """
        try:
            blob_name = blob_url.split(f"{self.container_name}/")[-1]
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            deletion_date = datetime.utcnow() + timedelta(days=days)
            metadata = {
                'delete_after': deletion_date.isoformat()
            }
            blob_client.set_blob_metadata(metadata)
            return True
        except Exception as e:
            print(f"Error scheduling deletion: {e}")
            return False

# Singleton instance
azure_blob_service = AzureBlobService()
```

### 4. Update Upload Endpoint in `main.py`
```python
from azure_blob_service import azure_blob_service

@app.post("/match-pair/{pair_id}/upload-proof", tags=["Proof"])
async def upload_proof(
    pair_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Upload proof of payment image for a match pair (funder only)"""
    try:
        pair = db.query(FundingMatchPair).filter(FundingMatchPair.id == uuid.UUID(pair_id)).first()
        if not pair:
            raise HTTPException(status_code=404, detail="Match pair not found")

        # Verify user is the funder
        funding_req = db.query(FundingRequest).filter(FundingRequest.id == pair.funding_request_id).first()
        if not funding_req:
            raise HTTPException(status_code=404, detail="Funding request not found")

        wallet = db.query(Wallet).filter(Wallet.id == funding_req.wallet_id).first()
        if str(wallet.user_id) != user_id:
            raise HTTPException(status_code=403, detail="You can only upload proof for your own matches")

        if pair.proof_uploaded:
            raise HTTPException(status_code=400, detail="Proof already uploaded")

        # Check if proof deadline has passed
        now = datetime.utcnow()
        if pair.proof_deadline and now > pair.proof_deadline:
            raise HTTPException(
                status_code=400,
                detail="Proof upload deadline has passed (4 hours). Contact admin."
            )

        # Validate file type
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )

        # Upload to Azure Blob Storage
        file_content = await file.read()
        content_type = file.content_type or "application/octet-stream"
        blob_url = azure_blob_service.upload_file(file_content, file.filename, content_type)

        # Update database
        pair.proof_uploaded = True
        pair.proof_url = blob_url
        pair.proof_uploaded_at = now
        pair.confirmation_deadline = now + timedelta(hours=4)
        db.commit()

        return SuccessResponse(
            message="Proof uploaded successfully. Waiting for confirmation...",
            data={
                "pair_id": str(pair.id),
                "proof_url": blob_url,
                "confirmation_deadline": pair.confirmation_deadline.isoformat()
            }
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e)})
```

### 5. Update Confirm Proof Endpoint
```python
@app.post("/match-pair/{pair_id}/confirm-proof", tags=["Proof"])
async def confirm_proof(
    pair_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Confirm receipt of payment for a match pair (withdrawer only)"""
    try:
        # ... existing verification code ...

        # Mark as confirmed
        pair.proof_confirmed = True
        pair.proof_confirmed_at = now
        pair.completed_at = now

        # ... existing balance update code ...

        # Schedule blob deletion for 7 days from now
        if pair.proof_url:
            azure_blob_service.schedule_deletion(pair.proof_url, days=7)

        db.commit()

        return SuccessResponse(
            message="Payment confirmed! Balances updated.",
            data={ /* ... */ }
        )
    except:
        # ... error handling ...
```

### 6. Background Task for Cleanup (create `blob_cleanup_task.py`)
```python
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from azure_blob_service import azure_blob_service

def cleanup_expired_blobs():
    """Delete blobs that have passed their deletion date"""
    try:
        container_client = azure_blob_service.container_client
        blobs = container_client.list_blobs(include=['metadata'])

        now = datetime.utcnow()
        for blob in blobs:
            if blob.metadata and 'delete_after' in blob.metadata:
                delete_after = datetime.fromisoformat(blob.metadata['delete_after'])
                if now >= delete_after:
                    print(f"Deleting expired blob: {blob.name}")
                    container_client.delete_blob(blob.name)
    except Exception as e:
        print(f"Error in cleanup task: {e}")

def start_cleanup_scheduler():
    """Run cleanup daily at midnight"""
    scheduler = BackgroundScheduler()
    scheduler.add_job(cleanup_expired_blobs, 'cron', hour=0, minute=0)
    scheduler.start()
    print("[OK] Blob cleanup scheduler started")
    return scheduler
```

### 7. Start Cleanup Scheduler in `main.py`
```python
from blob_cleanup_task import start_cleanup_scheduler

@app.on_event("startup")
async def startup_event():
    """Start schedulers on app startup"""
    # ... existing scheduler code ...

    # Start blob cleanup scheduler
    start_cleanup_scheduler()
```

## Frontend Changes

### 1. Update status page to use file input

Replace the Input component with a file input:

```tsx
<div className="space-y-2">
  <Label htmlFor={`proof-${matchedUser.pair_id}`}>
    Upload Proof of Payment
  </Label>
  <div className="flex gap-2">
    <Input
      id={`proof-${matchedUser.pair_id}`}
      type="file"
      accept="image/*,.pdf"
      onChange={(e) => {
        const file = e.target.files?.[0]
        if (file) {
          setSelectedFiles(prev => ({
            ...prev,
            [matchedUser.pair_id]: file
          }))
        }
      }}
      disabled={uploadingProof === matchedUser.pair_id}
    />
    <Button
      size="sm"
      onClick={() => handleUploadProof(matchedUser.pair_id)}
      disabled={uploadingProof === matchedUser.pair_id || !selectedFiles[matchedUser.pair_id]}
    >
      <Upload className="h-4 w-4 mr-1" />
      {uploadingProof === matchedUser.pair_id ? 'Uploading...' : 'Upload'}
    </Button>
  </div>
  <p className="text-xs text-gray-500">
    Accepted: Images (JPG, PNG, GIF, WebP) or PDF
  </p>
</div>
```

### 2. Update component state
```tsx
const [selectedFiles, setSelectedFiles] = useState<{ [key: string]: File | null }>({})

const handleUploadProof = async (pairId: string) => {
  const file = selectedFiles[pairId]
  if (!file) {
    alert('Please select a file')
    return
  }

  try {
    setUploadingProof(pairId)
    await fundingService.uploadProof(pairId, file)
    setSelectedFiles(prev => ({ ...prev, [pairId]: null }))
    alert('Proof uploaded successfully!')
    fetchRequests()
  } catch (err) {
    alert(handleApiError(err))
  } finally {
    setUploadingProof(null)
  }
}
```

## Azure Setup Steps

1. **Create Azure Storage Account**
   - Go to Azure Portal
   - Create a Storage Account
   - Note the connection string

2. **Create Container**
   - In the storage account, create a blob container named "payment-proofs"
   - Set access level to "Private"

3. **Configure CORS** (if accessing from browser)
   - In Storage Account settings → Resource Sharing (CORS)
   - Add rule allowing your frontend origin

4. **Add Connection String to Environment**
   - Copy connection string from Azure Portal
   - Add to `.env` file in funding-service directory

## Testing

1. Restart funding service with Azure credentials
2. Upload a payment proof image
3. Verify blob appears in Azure Portal
4. Confirm payment
5. Wait 7 days (or manually test cleanup task)
6. Verify blob is deleted

## Benefits

- **Scalable**: Azure Blob Storage can handle unlimited files
- **Cost-effective**: Pay only for storage used
- **Automatic cleanup**: Files deleted after 7 days
- **Secure**: Private container with SAS tokens for access
- **Reliable**: Built-in redundancy and availability
