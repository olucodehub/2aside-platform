"""
Referral Reward Logic
Handles paying 5% of platform fee to referrers when referred users win their first bet
"""

from decimal import Decimal
from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from shared import Wallet, WalletLog, ReferralReward, CurrencyType


def pay_referral_reward(
    db: Session,
    winner_wallet: Wallet,
    platform_fee: Decimal
) -> bool:
    """
    Pay referral reward to the referrer when a user wins their first bet.

    Args:
        db: Database session
        winner_wallet: The wallet of the user who just won
        platform_fee: The platform fee collected from this win

    Returns:
        bool: True if reward was paid, False if not eligible or error

    Logic:
        - Check if winner has won before (has_won_before = False)
        - Check if referral reward already paid (referral_reward_paid = False)
        - Check if winner was referred by someone (referred_by_wallet_id is not None)
        - Calculate reward: 5% of platform fee
        - Credit referrer's wallet
        - Create referral reward record
        - Mark winner as has_won_before = True and referral_reward_paid = True
    """

    try:
        # Check if winner is eligible for referral reward payout
        if winner_wallet.has_won_before:
            print(f"[Referral] Winner {winner_wallet.id} has won before, no reward")
            return False

        if winner_wallet.referral_reward_paid:
            print(f"[Referral] Reward already paid for winner {winner_wallet.id}")
            return False

        if not winner_wallet.referred_by_wallet_id:
            print(f"[Referral] Winner {winner_wallet.id} was not referred, no reward")
            # Still mark as won before
            winner_wallet.has_won_before = True
            db.commit()
            return False

        # Get referrer's wallet
        referrer_wallet = db.query(Wallet).filter(
            Wallet.id == winner_wallet.referred_by_wallet_id
        ).first()

        if not referrer_wallet:
            print(f"[Referral] Referrer wallet not found for {winner_wallet.id}")
            # Still mark as won before
            winner_wallet.has_won_before = True
            winner_wallet.referral_reward_paid = True
            db.commit()
            return False

        # Calculate reward: 5% of platform fee
        reward_amount = platform_fee * Decimal("0.05")

        if reward_amount <= 0:
            print(f"[Referral] Reward amount is 0 or negative: {reward_amount}")
            # Still mark as won before
            winner_wallet.has_won_before = True
            winner_wallet.referral_reward_paid = True
            db.commit()
            return False

        # Credit referrer's wallet
        old_balance = referrer_wallet.balance
        referrer_wallet.balance += reward_amount

        # Create wallet log for referrer
        referrer_log = WalletLog(
            id=uuid.uuid4(),
            wallet_id=referrer_wallet.id,
            transaction_type="referral_bonus",
            amount=reward_amount,
            balance_before=old_balance,
            balance_after=referrer_wallet.balance,
            description=f"Referral bonus from {winner_wallet.referral_code}'s first win",
            created_at=datetime.utcnow()
        )

        # Create referral reward record
        referral_reward = ReferralReward(
            id=uuid.uuid4(),
            referrer_wallet_id=referrer_wallet.id,
            referred_wallet_id=winner_wallet.id,
            amount=reward_amount,
            created_at=datetime.utcnow()
        )

        # Mark winner as has won before and reward paid
        winner_wallet.has_won_before = True
        winner_wallet.referral_reward_paid = True

        # Save all changes
        db.add(referrer_log)
        db.add(referral_reward)
        db.commit()

        print(f"[Referral] ✅ Paid {reward_amount} {referrer_wallet.currency} to referrer {referrer_wallet.id} from winner {winner_wallet.id}")

        return True

    except Exception as e:
        db.rollback()
        print(f"[Referral] ❌ Error paying referral reward: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_and_pay_referral_reward_on_win(
    db: Session,
    winner_wallet_id: str,
    platform_fee: Decimal
) -> bool:
    """
    Convenience function to check and pay referral reward.
    Call this function when a user wins a bet.

    Args:
        db: Database session
        winner_wallet_id: ID of the wallet that just won
        platform_fee: Platform fee collected from the win

    Returns:
        bool: True if reward was paid, False otherwise
    """

    try:
        winner_wallet = db.query(Wallet).filter(
            Wallet.id == uuid.UUID(winner_wallet_id)
        ).first()

        if not winner_wallet:
            print(f"[Referral] Winner wallet not found: {winner_wallet_id}")
            return False

        return pay_referral_reward(db, winner_wallet, platform_fee)

    except Exception as e:
        print(f"[Referral] Error in check_and_pay_referral_reward_on_win: {e}")
        return False
