"""
Background task scheduler for cleaning up expired Azure Blob Storage files
Runs daily at midnight to delete payment proofs older than 7 days after confirmation
"""

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from azure_blob_service import azure_blob_service
import logging

logger = logging.getLogger(__name__)


def cleanup_expired_blobs():
    """
    Delete blobs that have passed their deletion date
    This runs daily at midnight
    """
    logger.info("Starting scheduled blob cleanup task...")
    deleted_count = azure_blob_service.cleanup_expired_blobs()
    logger.info(f"Blob cleanup task completed: {deleted_count} blobs deleted")


def start_cleanup_scheduler():
    """
    Start the background scheduler for blob cleanup
    Runs daily at midnight (00:00)
    """
    scheduler = BackgroundScheduler()

    # Schedule cleanup at midnight every day
    scheduler.add_job(
        cleanup_expired_blobs,
        'cron',
        hour=0,
        minute=0,
        id='blob_cleanup',
        name='Azure Blob Cleanup Task',
        replace_existing=True
    )

    scheduler.start()
    logger.info("[OK] Blob cleanup scheduler started - will run daily at midnight")

    return scheduler


# Global scheduler instance
_cleanup_scheduler = None


def get_cleanup_scheduler():
    """Get or create the cleanup scheduler instance"""
    global _cleanup_scheduler
    if _cleanup_scheduler is None:
        _cleanup_scheduler = start_cleanup_scheduler()
    return _cleanup_scheduler
