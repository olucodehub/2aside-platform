"""
Celery Tasks for Batch Matching System
Smart amount splitting algorithm with admin wallet fallback
"""

from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Tuple, Dict
import uuid
import sys
import os
import pytz

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared import (
    SessionLocal,
    FundingRequest,
    WithdrawalRequest,
    FundingMatchPair,
    MergeCycle,
    AdminWallet,
    Wallet,
    User,
)

# Celery configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/1")

celery_app = Celery(
    "funding_batch_matching",
    broker=REDIS_URL,
    backend=REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)


# ========================================
# SMART MATCHING ALGORITHM
# ========================================

def smart_match_requests(
    funding_requests: List[FundingRequest],
    withdrawal_requests: List[WithdrawalRequest],
    db: Session
) -> List[Tuple[uuid.UUID, uuid.UUID, Decimal]]:
    """
    Smart matching algorithm that splits amounts to maximize matches.

    Returns: List of (funding_id, withdrawal_id, amount) tuples
    """
    matches = []

    # Sort by amount (ascending) for better splitting
    funding_sorted = sorted(funding_requests, key=lambda x: x.amount_remaining)
    withdrawal_sorted = sorted(withdrawal_requests, key=lambda x: x.amount_remaining)

    # Convert to mutable lists with remaining amounts
    funders = [[f.id, f.amount_remaining] for f in funding_sorted]
    withdrawers = [[w.id, w.amount_remaining] for w in withdrawal_sorted]

    i, j = 0, 0

    while i < len(funders) and j < len(withdrawers):
        funder_id, funder_remaining = funders[i]
        withdrawer_id, withdrawer_remaining = withdrawers[j]

        # Match the smaller amount
        match_amount = min(funder_remaining, withdrawer_remaining)

        matches.append((funder_id, withdrawer_id, match_amount))

        # Update remaining amounts
        funders[i][1] -= match_amount
        withdrawers[j][1] -= match_amount

        # Move to next if fully matched
        if funders[i][1] == 0:
            i += 1
        if withdrawers[j][1] == 0:
            j += 1

    return matches


def match_with_admin_wallet(
    unmatched_funding: List[FundingRequest],
    unmatched_withdrawal: List[WithdrawalRequest],
    currency: str,
    db: Session
) -> Tuple[List[Tuple[uuid.UUID, str, Decimal]], List[Tuple[str, uuid.UUID, Decimal]]]:
    """
    Match remaining requests with admin wallet.

    Returns:
        - List of (funding_id, 'admin', amount) for admin acting as withdrawer
        - List of ('admin', withdrawal_id, amount) for admin acting as funder
    """
    admin_as_withdrawer = []
    admin_as_funder = []

    # Get admin funding pool wallet
    admin_wallet = db.query(AdminWallet).filter(
        AdminWallet.wallet_type == "funding_pool",
        AdminWallet.currency == currency
    ).first()

    if not admin_wallet:
        return admin_as_withdrawer, admin_as_funder

    # Admin can fund unlimited (acts as withdrawer for users wanting to fund)
    for funding_req in unmatched_funding:
        if funding_req.amount_remaining > 0:
            admin_as_withdrawer.append((
                funding_req.id,
                'admin',
                funding_req.amount_remaining
            ))

    # Admin can withdraw only if balance available (acts as funder for users wanting to withdraw)
    admin_available = admin_wallet.balance
    for withdrawal_req in unmatched_withdrawal:
        if withdrawal_req.amount_remaining > 0 and admin_available >= withdrawal_req.amount_remaining:
            admin_as_funder.append((
                'admin',
                withdrawal_req.id,
                withdrawal_req.amount_remaining
            ))
            admin_available -= withdrawal_req.amount_remaining

    return admin_as_withdrawer, admin_as_funder


# ========================================
# CELERY TASKS
# ========================================

@celery_app.task(name="run_merge_cycle")
def run_merge_cycle(merge_cycle_id: str):
    """
    Execute a merge cycle - match all pending requests.
    This runs at scheduled times (9 AM, 3 PM, 9 PM).
    """
    db = SessionLocal()
    try:
        cycle = db.query(MergeCycle).filter(MergeCycle.id == uuid.UUID(merge_cycle_id)).first()
        if not cycle:
            print(f"Merge cycle {merge_cycle_id} not found")
            return

        if cycle.status != "pending":
            print(f"Merge cycle {merge_cycle_id} already processed")
            return

        print(f"\n{'='*60}")
        print(f"STARTING MERGE CYCLE: {cycle.scheduled_time}")
        print(f"{'='*60}\n")

        cycle.status = "processing"
        cycle.started_at = datetime.utcnow()
        db.commit()

        # Process each currency separately
        for currency in ["NAIRA", "USDT"]:
            print(f"\nProcessing {currency}...")

            # Get all pending requests for this currency
            funding_requests = db.query(FundingRequest).join(Wallet).filter(
                Wallet.currency == currency,
                FundingRequest.is_fully_matched == False,
                FundingRequest.is_completed == False,
                FundingRequest.requested_at < cycle.cutoff_time
            ).all()

            withdrawal_requests = db.query(WithdrawalRequest).join(Wallet).filter(
                Wallet.currency == currency,
                WithdrawalRequest.is_fully_matched == False,
                WithdrawalRequest.is_completed == False,
                WithdrawalRequest.requested_at < cycle.cutoff_time
            ).all()

            print(f"  Funding requests: {len(funding_requests)}")
            print(f"  Withdrawal requests: {len(withdrawal_requests)}")

            cycle.total_funding_requests += len(funding_requests)
            cycle.total_withdrawal_requests += len(withdrawal_requests)

            if not funding_requests and not withdrawal_requests:
                print(f"  No requests to process for {currency}")
                continue

            # Step 1: Smart match user-to-user
            user_matches = smart_match_requests(funding_requests, withdrawal_requests, db)
            print(f"  User-to-user matches: {len(user_matches)}")

            # Create match pairs
            for funding_id, withdrawal_id, amount in user_matches:
                now = datetime.utcnow()
                pair = FundingMatchPair(
                    id=uuid.uuid4(),
                    funding_request_id=funding_id,
                    withdrawal_request_id=withdrawal_id,
                    merge_cycle_id=cycle.id,
                    amount=amount,
                    proof_uploaded=False,
                    proof_confirmed=False,
                    proof_deadline=now + timedelta(hours=4),  # Funder has 4 hours to upload proof
                    funder_missed_deadline=False,
                    withdrawer_missed_deadline=False,
                    created_at=now
                )
                db.add(pair)

                # Update request amounts
                funding = db.query(FundingRequest).filter(FundingRequest.id == funding_id).first()
                withdrawal = db.query(WithdrawalRequest).filter(WithdrawalRequest.id == withdrawal_id).first()

                if funding:
                    funding.amount_remaining -= amount
                    if funding.amount_remaining == 0:
                        funding.is_fully_matched = True
                        funding.matched_at = datetime.utcnow()
                        funding.merge_cycle_id = cycle.id

                if withdrawal:
                    withdrawal.amount_remaining -= amount
                    if withdrawal.amount_remaining == 0:
                        withdrawal.is_fully_matched = True
                        withdrawal.matched_at = datetime.utcnow()
                        withdrawal.merge_cycle_id = cycle.id

                cycle.matched_pairs += 1

            db.commit()

            # Step 2: Get unmatched requests
            unmatched_funding = [f for f in funding_requests if f.amount_remaining > 0]
            unmatched_withdrawal = [w for w in withdrawal_requests if w.amount_remaining > 0]

            print(f"  Unmatched funding: {len(unmatched_funding)}")
            print(f"  Unmatched withdrawal: {len(unmatched_withdrawal)}")

            cycle.unmatched_funding += len(unmatched_funding)
            cycle.unmatched_withdrawal += len(unmatched_withdrawal)

            # Step 3: Match with admin wallet (FUTURE IMPLEMENTATION)
            # For now, unmatched requests wait for next cycle

            db.commit()

        # Mark cycle as completed
        cycle.status = "completed"
        cycle.completed_at = datetime.utcnow()
        db.commit()

        print(f"\n{'='*60}")
        print(f"MERGE CYCLE COMPLETED: {cycle.scheduled_time}")
        print(f"  Total matched pairs: {cycle.matched_pairs}")
        print(f"  Total unmatched funding: {cycle.unmatched_funding}")
        print(f"  Total unmatched withdrawal: {cycle.unmatched_withdrawal}")
        print(f"{'='*60}\n")

    except Exception as e:
        print(f"Error in merge cycle: {e}")
        import traceback
        traceback.print_exc()
        if cycle:
            cycle.status = "failed"
            db.commit()
    finally:
        db.close()


@celery_app.task(name="create_daily_merge_cycles")
def create_daily_merge_cycles():
    """
    Create merge cycles for the next 7 days.
    Runs daily at midnight.
    Times are in WAT (West Africa Time, UTC+1): 9 AM, 3 PM, 9 PM WAT
    """
    db = SessionLocal()
    try:
        print("\nCreating merge cycles for next 7 days...")

        # Define timezone (West Africa Time = UTC+1)
        wat = pytz.timezone('Africa/Lagos')
        merge_times = [9, 15, 21]  # 9 AM, 3 PM, 9 PM WAT

        # Get current time in WAT
        now_wat = datetime.now(wat)
        now_utc = datetime.utcnow()
        today_wat = now_wat.date()

        cycles_created = 0

        for day_offset in range(7):
            date = today_wat + timedelta(days=day_offset)

            for hour in merge_times:
                # Create time in WAT
                scheduled_time_wat = wat.localize(datetime(date.year, date.month, date.day, hour, 0, 0))
                # Convert to UTC for storage
                scheduled_time_utc = scheduled_time_wat.astimezone(pytz.utc).replace(tzinfo=None)

                # Skip if in the past
                if scheduled_time_utc < now_utc:
                    continue

                # Check if cycle already exists
                existing = db.query(MergeCycle).filter(
                    MergeCycle.scheduled_time == scheduled_time_utc
                ).first()

                if existing:
                    continue

                # Create new cycle (cutoff is 10 minutes before - users can cancel up to 10 mins before merge)
                cutoff_time = scheduled_time_utc - timedelta(minutes=10)
                join_window_closes = scheduled_time_utc + timedelta(minutes=5)

                cycle = MergeCycle(
                    id=uuid.uuid4(),
                    scheduled_time=scheduled_time_utc,
                    cutoff_time=cutoff_time,
                    join_window_closes=join_window_closes,
                    status="pending",
                    created_at=datetime.utcnow()
                )
                db.add(cycle)
                cycles_created += 1
                print(f"  Created cycle: {scheduled_time_wat.strftime('%Y-%m-%d %I:%M %p WAT')} (UTC: {scheduled_time_utc})")

        db.commit()
        print(f"Created {cycles_created} new merge cycles")

    except Exception as e:
        print(f"Error creating merge cycles: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


@celery_app.task(name="schedule_merge_cycle_execution")
def schedule_merge_cycle_execution():
    """
    Check if any merge cycles are ready to run and trigger them.
    Runs every minute.
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()

        # Find cycles that should run now
        ready_cycles = db.query(MergeCycle).filter(
            MergeCycle.scheduled_time <= now,
            MergeCycle.status == "pending"
        ).all()

        for cycle in ready_cycles:
            print(f"Triggering merge cycle: {cycle.scheduled_time}")
            run_merge_cycle.delay(str(cycle.id))

    except Exception as e:
        print(f"Error scheduling merge cycles: {e}")
    finally:
        db.close()


@celery_app.task(name="check_expired_deadlines")
def check_expired_deadlines():
    """
    Check for expired deadlines and block users who miss them.
    Runs every minute via Celery Beat.
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        print(f"\n[{now}] Checking for expired deadlines...")

        # Find pairs where proof deadline has passed (funder didn't upload proof in time)
        expired_proof_pairs = db.query(FundingMatchPair).filter(
            FundingMatchPair.proof_deadline <= now,
            FundingMatchPair.proof_uploaded == False,
            FundingMatchPair.funder_missed_deadline == False  # Not yet flagged
        ).all()

        if expired_proof_pairs:
            print(f"  Found {len(expired_proof_pairs)} expired proof deadlines")

        for pair in expired_proof_pairs:
            # Mark as missed
            pair.funder_missed_deadline = True

            # Get funder's wallet and block it
            funding_req = db.query(FundingRequest).filter(
                FundingRequest.id == pair.funding_request_id
            ).first()

            if funding_req:
                wallet = db.query(Wallet).filter(Wallet.id == funding_req.wallet_id).first()
                if wallet and not wallet.is_blocked:
                    wallet.is_blocked = True
                    user = db.query(User).filter(User.id == wallet.user_id).first()
                    print(f"  ⚠️  BLOCKED FUNDER: {user.username if user else 'Unknown'} (missed proof upload deadline)")

        # Find pairs where confirmation deadline has passed (withdrawer didn't confirm in time)
        expired_confirmation_pairs = db.query(FundingMatchPair).filter(
            FundingMatchPair.confirmation_deadline <= now,
            FundingMatchPair.proof_uploaded == True,
            FundingMatchPair.proof_confirmed == False,
            FundingMatchPair.withdrawer_missed_deadline == False  # Not yet flagged
        ).all()

        if expired_confirmation_pairs:
            print(f"  Found {len(expired_confirmation_pairs)} expired confirmation deadlines")

        for pair in expired_confirmation_pairs:
            # Mark as missed
            pair.withdrawer_missed_deadline = True

            # Get withdrawer's wallet and block it
            withdrawal_req = db.query(WithdrawalRequest).filter(
                WithdrawalRequest.id == pair.withdrawal_request_id
            ).first()

            if withdrawal_req:
                wallet = db.query(Wallet).filter(Wallet.id == withdrawal_req.wallet_id).first()
                if wallet and not wallet.is_blocked:
                    wallet.is_blocked = True
                    user = db.query(User).filter(User.id == wallet.user_id).first()
                    print(f"  ⚠️  BLOCKED WITHDRAWER: {user.username if user else 'Unknown'} (missed confirmation deadline)")

        db.commit()

        if expired_proof_pairs or expired_confirmation_pairs:
            print(f"  ✅ Processed {len(expired_proof_pairs) + len(expired_confirmation_pairs)} expired deadlines")

    except Exception as e:
        db.rollback()
        print(f"  ❌ Error checking deadlines: {e}")
    finally:
        db.close()


# ========================================
# CELERY BEAT SCHEDULE
# ========================================

celery_app.conf.beat_schedule = {
    "schedule-merge-cycles": {
        "task": "schedule_merge_cycle_execution",
        "schedule": 60.0,  # Every minute
    },
    "create-daily-cycles": {
        "task": "create_daily_merge_cycles",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight
    },
    "check-expired-deadlines": {
        "task": "check_expired_deadlines",
        "schedule": 60.0,  # Every minute - check for expired deadlines and auto-block users
    },
}
