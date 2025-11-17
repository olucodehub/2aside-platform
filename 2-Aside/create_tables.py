"""
Create all database tables
"""
import sys
import os

# Load .env file
def load_env():
    env_vars = {}
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                env_vars[key] = value
    return env_vars

print("Loading environment variables...")
env_vars = load_env()

# Import after loading env
from shared.database import Base, engine
from shared import models

print(f"\nConnecting to database...")
print(f"Database: {os.getenv('DATABASE_URL', 'Not set')[:50]}...")

try:
    # Create all tables
    print("\nCreating tables...")
    Base.metadata.create_all(bind=engine)

    print("\n✓ All tables created successfully!")
    print("\nTables created:")
    print("  ✓ Users")
    print("  ✓ Wallets")
    print("  ✓ BankDetails")
    print("  ✓ WalletLog")
    print("  ✓ ReferralReward")
    print("  ✓ Games")
    print("  ✓ BetRegistrations")
    print("  ✓ BetQueue")
    print("  ✓ MatchPairs")
    print("  ✓ FundingRequests (updated for batch matching)")
    print("  ✓ WithdrawalRequests (updated for batch matching)")
    print("  ✓ FundingMatchPairs (new)")
    print("  ✓ MergeCycles (new)")
    print("  ✓ AdminWallets (new)")

except Exception as e:
    print(f"\n✗ Error creating tables: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
