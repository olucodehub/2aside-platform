"""
Add deadline fields to FundingMatchPair table
Run this after updating the models to add the new deadline tracking fields
"""

from sqlalchemy import text
from shared import engine

def add_deadline_fields():
    """Add new deadline fields to funding_match_pairs table"""

    with engine.connect() as conn:
        print("Adding deadline fields to funding_match_pairs table...")

        fields = [
            ("proof_uploaded_at", "DATETIME NULL"),
            ("proof_confirmed_at", "DATETIME NULL"),
            ("proof_deadline", "DATETIME NULL"),
            ("confirmation_deadline", "DATETIME NULL"),
            ("funder_missed_deadline", "BIT NOT NULL DEFAULT 0"),
            ("withdrawer_missed_deadline", "BIT NOT NULL DEFAULT 0"),
        ]

        for field_name, field_type in fields:
            try:
                print(f"Adding {field_name} column...")
                conn.execute(text(f"ALTER TABLE funding_match_pairs ADD {field_name} {field_type}"))
                conn.commit()
                print(f"✅ {field_name} column added!")
            except Exception as e:
                print(f"⚠️  Error adding {field_name} (might already exist): {e}")
                conn.rollback()

        print("\n✅ All deadline fields migration complete!")

if __name__ == "__main__":
    add_deadline_fields()
    print("\n🎉 Migration complete!")
