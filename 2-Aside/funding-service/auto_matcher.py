"""
Automatic merge cycle matcher using APScheduler.
Runs matching at 9am, 3pm, 9pm WAT daily.
No Celery, no pre-created merge cycles - just real-time scheduling.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared import SessionLocal, FundingRequest, WithdrawalRequest, FundingMatchPair, Wallet, MergeCycle
from merge_scheduler import WAT, MERGE_TIMES
import logging
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_matching():
    """
    Execute the batch matching process.
    This is called automatically at 9am, 3pm, 9pm WAT.
    """
    from celery_batch_matching import smart_match_requests

    db = SessionLocal()
    try:
        now_wat = datetime.now(WAT)
        now_utc = datetime.utcnow()
        logger.info(f"=== AUTO MATCHING STARTED at {now_wat.strftime('%I:%M %p WAT')} ===")

        # Create a merge cycle for this manual trigger
        merge_cycle = MergeCycle(
            id=uuid.uuid4(),
            scheduled_time=now_utc,
            cutoff_time=now_utc,  # No cutoff for manual triggers
            status="processing",
            started_at=now_utc,
            total_funding_requests=0,
            total_withdrawal_requests=0,
            matched_pairs=0,
            unmatched_funding=0,
            unmatched_withdrawal=0
        )
        db.add(merge_cycle)
        db.flush()  # Get the ID
        logger.info(f"Created merge cycle: {merge_cycle.id}")

        # Run matching for both currencies
        for currency in ["NAIRA", "USDT"]:
            logger.info(f"Running matching for {currency}...")

            # Get all pending requests for this currency
            funding_requests = db.query(FundingRequest).join(Wallet).filter(
                Wallet.currency == currency,
                FundingRequest.is_fully_matched == False,
                FundingRequest.is_completed == False
            ).all()

            withdrawal_requests = db.query(WithdrawalRequest).join(Wallet).filter(
                Wallet.currency == currency,
                WithdrawalRequest.is_fully_matched == False,
                WithdrawalRequest.is_completed == False
            ).all()

            logger.info(f"  Funding requests: {len(funding_requests)}")
            logger.info(f"  Withdrawal requests: {len(withdrawal_requests)}")

            if not funding_requests or not withdrawal_requests:
                logger.info(f"  No requests to match for {currency}")
                continue

            # Run smart matching algorithm
            user_matches = smart_match_requests(funding_requests, withdrawal_requests, db)
            logger.info(f"  Created {len(user_matches)} matches")

            # Update merge cycle stats
            merge_cycle.total_funding_requests += len(funding_requests)
            merge_cycle.total_withdrawal_requests += len(withdrawal_requests)

            # Create match pairs
            for funding_id, withdrawal_id, amount in user_matches:
                pair = FundingMatchPair(
                    id=uuid.uuid4(),
                    funding_request_id=funding_id,
                    withdrawal_request_id=withdrawal_id,
                    merge_cycle_id=merge_cycle.id,  # Use the created merge cycle
                    amount=amount,
                    proof_uploaded=False,
                    proof_confirmed=False,
                    proof_deadline=now_utc + timedelta(hours=4),
                    funder_missed_deadline=False,
                    withdrawer_missed_deadline=False,
                    created_at=now_utc
                )
                db.add(pair)
                merge_cycle.matched_pairs += 1

                # Update request amounts
                funding = db.query(FundingRequest).filter(FundingRequest.id == funding_id).first()
                withdrawal = db.query(WithdrawalRequest).filter(WithdrawalRequest.id == withdrawal_id).first()

                if funding:
                    funding.amount_remaining -= amount
                    if funding.amount_remaining == 0:
                        funding.is_fully_matched = True
                        funding.matched_at = now_utc
                        funding.merge_cycle_id = merge_cycle.id

                if withdrawal:
                    withdrawal.amount_remaining -= amount
                    if withdrawal.amount_remaining == 0:
                        withdrawal.is_fully_matched = True
                        withdrawal.matched_at = now_utc
                        withdrawal.merge_cycle_id = merge_cycle.id

        # Mark cycle as completed
        merge_cycle.status = "completed"
        merge_cycle.completed_at = now_utc
        db.commit()

        logger.info(f"=== AUTO MATCHING COMPLETED ===")
        logger.info(f"  Matched pairs: {merge_cycle.matched_pairs}")
    except Exception as e:
        logger.error(f"Error during auto matching: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


def start_scheduler():
    """
    Start the background scheduler for automatic matching.
    Schedules matching at 9am, 3pm, 9pm WAT daily.
    """
    scheduler = BackgroundScheduler(timezone=WAT)

    # Schedule matching at each merge time
    for merge_time in MERGE_TIMES:
        hour = merge_time.hour
        minute = merge_time.minute

        # Create cron trigger for this time
        trigger = CronTrigger(
            hour=hour,
            minute=minute,
            timezone=WAT
        )

        scheduler.add_job(
            run_matching,
            trigger=trigger,
            id=f"match_{hour:02d}_{minute:02d}",
            name=f"Auto Match at {hour:02d}:{minute:02d} WAT",
            replace_existing=True
        )

        logger.info(f"Scheduled automatic matching at {hour:02d}:{minute:02d} WAT")

    scheduler.start()
    logger.info("Auto-matching scheduler started successfully")

    return scheduler


# Global scheduler instance
_scheduler = None


def get_scheduler():
    """Get or create the scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = start_scheduler()
    return _scheduler
