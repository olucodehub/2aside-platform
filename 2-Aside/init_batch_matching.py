"""
Initialize Batch Matching System
- Create admin wallets
- Create initial merge cycles
- Run this after create_tables.py
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import uuid

# Load .env
def load_env():
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

print("Loading environment variables...")
load_env()

from shared import SessionLocal, AdminWallet, MergeCycle

def init_admin_wallets(db):
    """Create admin wallets for both currencies"""
    print("\n" + "="*60)
    print("CREATING ADMIN WALLETS")
    print("="*60)

    wallets_created = 0

    for currency in ["NAIRA", "USDT"]:
        # Funding pool wallet
        funding_pool = db.query(AdminWallet).filter(
            AdminWallet.wallet_type == "funding_pool",
            AdminWallet.currency == currency
        ).first()

        if not funding_pool:
            funding_pool = AdminWallet(
                id=uuid.uuid4(),
                wallet_type="funding_pool",
                currency=currency,
                balance=Decimal("0"),
                total_funded=Decimal("0"),
                total_received=Decimal("0"),
                created_at=datetime.utcnow()
            )
            db.add(funding_pool)
            wallets_created += 1
            print(f"  ✓ Created funding_pool wallet for {currency}")
        else:
            print(f"  - funding_pool wallet for {currency} already exists")

        # Platform fees wallet
        platform_fees = db.query(AdminWallet).filter(
            AdminWallet.wallet_type == "platform_fees",
            AdminWallet.currency == currency
        ).first()

        if not platform_fees:
            platform_fees = AdminWallet(
                id=uuid.uuid4(),
                wallet_type="platform_fees",
                currency=currency,
                balance=Decimal("0"),
                total_fees_collected=Decimal("0"),
                created_at=datetime.utcnow()
            )
            db.add(platform_fees)
            wallets_created += 1
            print(f"  ✓ Created platform_fees wallet for {currency}")
        else:
            print(f"  - platform_fees wallet for {currency} already exists")

    db.commit()
    print(f"\nAdmin wallets created: {wallets_created}")
    return wallets_created


def init_merge_cycles(db):
    """Create merge cycles for next 7 days"""
    print("\n" + "="*60)
    print("CREATING MERGE CYCLES")
    print("="*60)

    merge_times = [9, 15, 21]  # 9 AM, 3 PM, 9 PM
    today = datetime.utcnow().date()

    cycles_created = 0

    for day_offset in range(7):
        date = today + timedelta(days=day_offset)
        print(f"\nDate: {date}")

        for hour in merge_times:
            scheduled_time = datetime(date.year, date.month, date.day, hour, 0, 0)

            # Skip if in the past
            if scheduled_time < datetime.utcnow():
                print(f"  - {hour}:00 - Skipped (in the past)")
                continue

            # Check if exists
            existing = db.query(MergeCycle).filter(
                MergeCycle.scheduled_time == scheduled_time
            ).first()

            if existing:
                print(f"  - {hour}:00 - Already exists")
                continue

            # Create cycle
            cutoff_time = scheduled_time - timedelta(hours=1)

            cycle = MergeCycle(
                id=uuid.uuid4(),
                scheduled_time=scheduled_time,
                cutoff_time=cutoff_time,
                status="pending",
                total_funding_requests=0,
                total_withdrawal_requests=0,
                matched_pairs=0,
                unmatched_funding=0,
                unmatched_withdrawal=0,
                admin_funded=0,
                admin_withdrew=0,
                created_at=datetime.utcnow()
            )
            db.add(cycle)
            cycles_created += 1
            print(f"  ✓ {hour}:00 - Created (cutoff: {cutoff_time.strftime('%H:%M')})")

    db.commit()
    print(f"\nMerge cycles created: {cycles_created}")
    return cycles_created


def main():
    print("\n" + "="*60)
    print("BATCH MATCHING SYSTEM INITIALIZATION")
    print("="*60)

    db = SessionLocal()

    try:
        # Step 1: Create admin wallets
        wallets = init_admin_wallets(db)

        # Step 2: Create merge cycles
        cycles = init_merge_cycles(db)

        print("\n" + "="*60)
        print("INITIALIZATION COMPLETE")
        print("="*60)
        print(f"  Admin wallets: {wallets}")
        print(f"  Merge cycles: {cycles}")
        print("\nBatch matching system is ready!")
        print("\nNext steps:")
        print("  1. Start funding service: python funding-service/main.py")
        print("  2. Start Celery worker: celery -A funding-service.celery_batch_matching worker --loglevel=info")
        print("  3. Start Celery beat: celery -A funding-service.celery_batch_matching beat --loglevel=info")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
