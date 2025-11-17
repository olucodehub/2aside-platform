"""
Update existing funding_requests and withdrawal_requests tables
Add new columns required for batch matching system
"""

from sqlalchemy import text
from shared import engine

def update_funding_requests_table():
    """Add batch matching columns to funding_requests table"""

    with engine.connect() as conn:
        print("Updating funding_requests table...")

        fields = [
            ("amount_remaining", "DECIMAL(18, 2) NULL"),
            ("is_fully_matched", "BIT NOT NULL DEFAULT 0"),
            ("is_completed", "BIT NOT NULL DEFAULT 0"),
            ("merge_cycle_id", "UNIQUEIDENTIFIER NULL"),
            ("matched_at", "DATETIME NULL"),
        ]

        for field_name, field_type in fields:
            try:
                print(f"  Adding {field_name} column...")
                conn.execute(text(f"ALTER TABLE funding_requests ADD {field_name} {field_type}"))
                conn.commit()
                print(f"  ✅ {field_name} column added!")
            except Exception as e:
                print(f"  ⚠️  Error adding {field_name} (might already exist): {e}")
                conn.rollback()

        # Set amount_remaining = amount for existing records
        try:
            print("\n  Setting amount_remaining = amount for existing records...")
            conn.execute(text("""
                UPDATE funding_requests
                SET amount_remaining = amount
                WHERE amount_remaining IS NULL
            """))
            conn.commit()
            print("  ✅ Updated existing records!")
        except Exception as e:
            print(f"  ⚠️  Error updating existing records: {e}")
            conn.rollback()

        print("✅ funding_requests table updated!\n")


def update_withdrawal_requests_table():
    """Add batch matching columns to withdrawal_requests table"""

    with engine.connect() as conn:
        print("Updating withdrawal_requests table...")

        fields = [
            ("amount_remaining", "DECIMAL(18, 2) NULL"),
            ("is_fully_matched", "BIT NOT NULL DEFAULT 0"),
            ("is_completed", "BIT NOT NULL DEFAULT 0"),
            ("merge_cycle_id", "UNIQUEIDENTIFIER NULL"),
            ("matched_at", "DATETIME NULL"),
        ]

        for field_name, field_type in fields:
            try:
                print(f"  Adding {field_name} column...")
                conn.execute(text(f"ALTER TABLE withdrawal_requests ADD {field_name} {field_type}"))
                conn.commit()
                print(f"  ✅ {field_name} column added!")
            except Exception as e:
                print(f"  ⚠️  Error adding {field_name} (might already exist): {e}")
                conn.rollback()

        # Set amount_remaining = amount for existing records
        try:
            print("\n  Setting amount_remaining = amount for existing records...")
            conn.execute(text("""
                UPDATE withdrawal_requests
                SET amount_remaining = amount
                WHERE amount_remaining IS NULL
            """))
            conn.commit()
            print("  ✅ Updated existing records!")
        except Exception as e:
            print(f"  ⚠️  Error updating existing records: {e}")
            conn.rollback()

        print("✅ withdrawal_requests table updated!\n")


def add_indexes():
    """Add indexes for performance"""

    with engine.connect() as conn:
        print("Adding indexes...")

        indexes = [
            ("idx_funding_wallet_match", "funding_requests", "(wallet_id, is_fully_matched)"),
            ("idx_withdrawal_wallet_match", "withdrawal_requests", "(wallet_id, is_fully_matched)"),
        ]

        for index_name, table_name, columns in indexes:
            try:
                print(f"  Creating index {index_name}...")
                conn.execute(text(f"CREATE INDEX {index_name} ON {table_name} {columns}"))
                conn.commit()
                print(f"  ✅ Index {index_name} created!")
            except Exception as e:
                print(f"  ⚠️  Error creating index {index_name} (might already exist): {e}")
                conn.rollback()

        print("✅ Indexes added!\n")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("UPDATING FUNDING & WITHDRAWAL TABLES FOR BATCH MATCHING")
    print("="*60 + "\n")

    try:
        # Update tables
        update_funding_requests_table()
        update_withdrawal_requests_table()

        # Add indexes
        add_indexes()

        print("="*60)
        print("✅ ALL UPDATES COMPLETE!")
        print("="*60)
        print("\nYour funding_requests and withdrawal_requests tables")
        print("are now ready for the batch matching system!")
        print("\nNext: Run 'python init_batch_matching.py' to initialize")
        print("merge cycles and admin wallets.")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
