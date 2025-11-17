"""
Add first_name and last_name fields to users table
Run this migration to add the new name fields required for bank account validation
"""

from sqlalchemy import text
from shared import engine

def add_user_name_fields():
    """Add first_name and last_name columns to users table"""

    with engine.connect() as conn:
        print("Adding first_name and last_name fields to users table...")

        # Add first_name column
        try:
            print("Adding first_name column...")
            conn.execute(text("ALTER TABLE users ADD first_name NVARCHAR(100) NULL"))
            conn.commit()
            print("✅ first_name column added!")
        except Exception as e:
            print(f"⚠️  Error adding first_name (might already exist): {e}")
            conn.rollback()

        # Add last_name column
        try:
            print("Adding last_name column...")
            conn.execute(text("ALTER TABLE users ADD last_name NVARCHAR(100) NULL"))
            conn.commit()
            print("✅ last_name column added!")
        except Exception as e:
            print(f"⚠️  Error adding last_name (might already exist): {e}")
            conn.rollback()

        print("\n✅ Migration complete!")
        print("\n⚠️  IMPORTANT: Existing users will have NULL values for first_name and last_name.")
        print("You should either:")
        print("1. Update existing users manually to add their names")
        print("2. Or require them to update their profile with their names")
        print("\nFor new registrations, these fields will be required.")

if __name__ == "__main__":
    add_user_name_fields()
    print("\n🎉 Migration complete!")
