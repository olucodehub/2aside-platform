"""
Azure Blob Storage Service for Payment Proof Uploads
Handles file uploads, deletions, and scheduled cleanup
"""

from azure.storage.blob import BlobServiceClient, ContentSettings
from datetime import datetime, timedelta
import os
import uuid
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AzureBlobService:
    def __init__(self):
        self.connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME", "payment-proofs")

        if not self.connection_string:
            logger.warning("AZURE_STORAGE_CONNECTION_STRING not set. Blob storage will not work.")
            self.blob_service_client = None
            self.container_client = None
            return

        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            self.container_client = self.blob_service_client.get_container_client(self.container_name)

            # Create container if it doesn't exist
            if not self.container_client.exists():
                self.container_client.create_container()
                logger.info(f"Created blob container: {self.container_name}")
            else:
                logger.info(f"Using existing blob container: {self.container_name}")
        except Exception as e:
            logger.error(f"Error initializing Azure Blob Service: {e}")
            self.blob_service_client = None
            self.container_client = None

    def upload_file(self, file_content: bytes, filename: str, content_type: str = "image/jpeg") -> str:
        """
        Upload file to Azure Blob Storage
        Returns the blob URL
        """
        if not self.blob_service_client:
            raise Exception("Azure Blob Storage not configured")

        # Generate unique blob name
        file_ext = Path(filename).suffix.lower()
        blob_name = f"{uuid.uuid4()}{file_ext}"

        # Upload blob
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )

        content_settings = ContentSettings(content_type=content_type)

        blob_client.upload_blob(
            file_content,
            content_settings=content_settings,
            overwrite=True
        )

        logger.info(f"Uploaded blob: {blob_name}")

        # Return the blob URL
        return blob_client.url

    def delete_blob(self, blob_url: str) -> bool:
        """Delete a blob from storage"""
        if not self.blob_service_client:
            logger.warning("Azure Blob Storage not configured")
            return False

        try:
            # Extract blob name from URL
            blob_name = blob_url.split(f"{self.container_name}/")[-1]
            # Remove query parameters if present
            blob_name = blob_name.split("?")[0]

            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            logger.info(f"Deleted blob: {blob_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting blob: {e}")
            return False

    def schedule_deletion(self, blob_url: str, days: int = 7) -> bool:
        """
        Set blob metadata with deletion date
        A background task will clean up expired blobs
        """
        if not self.blob_service_client:
            logger.warning("Azure Blob Storage not configured")
            return False

        try:
            # Extract blob name from URL
            blob_name = blob_url.split(f"{self.container_name}/")[-1]
            blob_name = blob_name.split("?")[0]

            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            deletion_date = datetime.utcnow() + timedelta(days=days)
            metadata = {
                'delete_after': deletion_date.isoformat()
            }
            blob_client.set_blob_metadata(metadata)
            logger.info(f"Scheduled deletion for blob {blob_name} on {deletion_date}")
            return True
        except Exception as e:
            logger.error(f"Error scheduling deletion: {e}")
            return False

    def cleanup_expired_blobs(self) -> int:
        """
        Delete blobs that have passed their deletion date
        Returns number of blobs deleted
        """
        if not self.container_client:
            logger.warning("Azure Blob Storage not configured")
            return 0

        deleted_count = 0
        try:
            blobs = self.container_client.list_blobs(include=['metadata'])
            now = datetime.utcnow()

            for blob in blobs:
                if blob.metadata and 'delete_after' in blob.metadata:
                    try:
                        delete_after = datetime.fromisoformat(blob.metadata['delete_after'])
                        if now >= delete_after:
                            logger.info(f"Deleting expired blob: {blob.name}")
                            self.container_client.delete_blob(blob.name)
                            deleted_count += 1
                    except Exception as e:
                        logger.error(f"Error processing blob {blob.name}: {e}")
                        continue

            if deleted_count > 0:
                logger.info(f"Cleanup complete: deleted {deleted_count} expired blobs")
            else:
                logger.info("Cleanup complete: no expired blobs found")

        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")

        return deleted_count


# Singleton instance
azure_blob_service = AzureBlobService()
