"""
Celery Application for Funding Service
Background tasks for matching, expiration, and notifications
"""

from celery import Celery
from celery.schedules import crontab
import os
from datetime import datetime, timedelta
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Initialize Celery
celery_app = Celery(
    "funding_service",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)

# Periodic task schedule
celery_app.conf.beat_schedule = {
    # Expire old funding/withdrawal requests every 10 minutes
    "expire-old-requests": {
        "task": "funding_service.celery_app.expire_old_requests",
        "schedule": 600.0,  # 10 minutes
    },
    # Try to match pending requests every 5 minutes
    "match-pending-requests": {
        "task": "funding_service.celery_app.match_pending_requests",
        "schedule": 300.0,  # 5 minutes
    },
}


# ========================================
# TASK: EXPIRE OLD REQUESTS
# ========================================

@celery_app.task(name="funding_service.celery_app.expire_old_requests")
def expire_old_requests():
    """
    Expire funding and withdrawal requests that have passed their expiration time.
    Runs every 10 minutes.
    """
    from shared.database import SessionLocal
    from shared.models import FundingRequest, WithdrawalRequest
    from shared.constants import FundingRequestStatus, WithdrawalRequestStatus

    db = SessionLocal()

    try:
        now = datetime.utcnow()

        # Expire funding requests
        expired_funding = db.query(FundingRequest).filter(
            FundingRequest.status == FundingRequestStatus.PENDING,
            FundingRequest.expires_at <= now
        ).all()

        for req in expired_funding:
            req.status = FundingRequestStatus.EXPIRED

        # Expire withdrawal requests
        expired_withdrawal = db.query(WithdrawalRequest).filter(
            WithdrawalRequest.status == WithdrawalRequestStatus.PENDING,
            WithdrawalRequest.expires_at <= now
        ).all()

        for req in expired_withdrawal:
            req.status = WithdrawalRequestStatus.EXPIRED

        db.commit()

        return {
            "expired_funding": len(expired_funding),
            "expired_withdrawal": len(expired_withdrawal),
            "timestamp": now.isoformat()
        }

    except Exception as e:
        db.rollback()
        return {"error": str(e)}

    finally:
        db.close()


# ========================================
# TASK: MATCH PENDING REQUESTS
# ========================================

@celery_app.task(name="funding_service.celery_app.match_pending_requests")
def match_pending_requests():
    """
    Try to match pending funding requests with pending withdrawal requests.
    Runs every 5 minutes.
    """
    from shared.database import SessionLocal
    from shared.models import FundingRequest, WithdrawalRequest, FundingMatch
    from shared.constants import (
        FundingRequestStatus,
        WithdrawalRequestStatus,
        FundingMatchStatus
    )

    db = SessionLocal()

    try:
        now = datetime.utcnow()
        matches_created = 0

        # Get all pending funding requests
        pending_funding = db.query(FundingRequest).filter(
            FundingRequest.status == FundingRequestStatus.PENDING,
            FundingRequest.expires_at > now
        ).all()

        for funding_req in pending_funding:
            # Try to find matching withdrawal request
            withdrawal_req = db.query(WithdrawalRequest).filter(
                WithdrawalRequest.amount == funding_req.amount,
                WithdrawalRequest.currency == funding_req.currency,
                WithdrawalRequest.status == WithdrawalRequestStatus.PENDING,
                WithdrawalRequest.expires_at > now
            ).first()

            if withdrawal_req:
                # Create match
                import uuid
                match = FundingMatch(
                    id=uuid.uuid4(),
                    funder_wallet_id=funding_req.wallet_id,
                    withdrawer_wallet_id=withdrawal_req.wallet_id,
                    amount=funding_req.amount,
                    currency=funding_req.currency,
                    status=FundingMatchStatus.MATCHED,
                    proof_uploaded=False,
                    proof_confirmed=False,
                    created_at=now
                )

                db.add(match)

                # Update request statuses
                funding_req.status = FundingRequestStatus.MATCHED
                funding_req.match_id = match.id

                withdrawal_req.status = WithdrawalRequestStatus.MATCHED
                withdrawal_req.match_id = match.id

                matches_created += 1

        db.commit()

        return {
            "matches_created": matches_created,
            "pending_funding_checked": len(pending_funding),
            "timestamp": now.isoformat()
        }

    except Exception as e:
        db.rollback()
        return {"error": str(e)}

    finally:
        db.close()


# ========================================
# TASK: SEND NOTIFICATION
# ========================================

@celery_app.task(name="funding_service.celery_app.send_notification")
def send_notification(user_id: str, notification_type: str, message: str):
    """
    Send notification to user (email, SMS, push).
    This is a placeholder - implement actual notification logic here.
    """
    # TODO: Implement notification sending
    # - Email via SendGrid/SES
    # - SMS via Twilio
    # - Push via Firebase Cloud Messaging

    return {
        "user_id": user_id,
        "type": notification_type,
        "message": message,
        "sent_at": datetime.utcnow().isoformat(),
        "status": "queued"  # Would be "sent" in production
    }


# ========================================
# TASK: CLEANUP OLD MATCHES
# ========================================

@celery_app.task(name="funding_service.celery_app.cleanup_old_matches")
def cleanup_old_matches():
    """
    Archive old confirmed/cancelled matches (older than 90 days).
    This keeps the database performant.
    """
    from shared.database import SessionLocal
    from shared.models import FundingMatch
    from shared.constants import FundingMatchStatus

    db = SessionLocal()

    try:
        cutoff_date = datetime.utcnow() - timedelta(days=90)

        # Find old completed matches
        old_matches = db.query(FundingMatch).filter(
            FundingMatch.status.in_([
                FundingMatchStatus.CONFIRMED,
                FundingMatchStatus.CANCELLED
            ]),
            FundingMatch.created_at <= cutoff_date
        ).all()

        # In production, move to archive table instead of deleting
        # For now, we'll just count them
        archived_count = len(old_matches)

        return {
            "archived_matches": archived_count,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {"error": str(e)}

    finally:
        db.close()
