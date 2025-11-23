"""
2-Aside Platform - Shared Database Models
Core models used across all microservices
"""

from sqlalchemy import Column, String, Integer, Numeric, Boolean, DateTime, ForeignKey, Enum, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
import uuid
from datetime import datetime
import enum

from .database import Base

# Use MSSQL UNIQUEIDENTIFIER for SQL Server compatibility
UUID = UNIQUEIDENTIFIER


# ========================================
# ENUMS
# ========================================

class CurrencyEnum(str, enum.Enum):
    """Currency types supported"""
    NAIRA = "NAIRA"
    USDT = "USDT"


class TransactionTypeEnum(str, enum.Enum):
    """Transaction log types"""
    WIN = "win"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    REFERRAL_BONUS = "referral_bonus"
    PLATFORM_FEE = "platform_fee"
    BET_DEBIT = "bet_debit"
    BET_REFUND = "bet_refund"


# ========================================
# USER & AUTHENTICATION
# ========================================

class User(Base):
    """
    User model - Authentication and referral
    Wallet-specific data is in Wallet model
    """
    __tablename__ = "users"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    password_hash = Column(String(255), nullable=False)
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    referred_by_user_id = Column(UUID(), ForeignKey("users.id"), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    wallets = relationship("Wallet", back_populates="user", cascade="all, delete-orphan")
    referred_users = relationship("User", backref="referrer", remote_side=[id])

    def __repr__(self):
        return f"<User {self.username} ({self.email})>"


# ========================================
# WALLET & CURRENCY SEPARATION
# ========================================

class Wallet(Base):
    """
    Wallet model - Separate instance per currency
    Each user can have up to 2 wallets (Naira + USDT)
    """
    __tablename__ = "wallets"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(), ForeignKey("users.id"), nullable=False)
    currency = Column(Enum(CurrencyEnum), nullable=False)

    # Balance
    balance = Column(Numeric(18, 2), default=0, nullable=False)
    total_deposited = Column(Numeric(18, 2), default=0, nullable=False)
    total_won = Column(Numeric(18, 2), default=0, nullable=False)

    # Behavior tracking (separate per currency)
    consecutive_cancellations = Column(Integer, default=0, nullable=False)
    consecutive_misses = Column(Integer, default=0, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    block_reason = Column(String(500), nullable=True)  # Reason for blocking

    # Referral (separate per currency)
    referred_by_wallet_id = Column(UUID(), ForeignKey("wallets.id"), nullable=True)
    has_won_before = Column(Boolean, default=False, nullable=False)
    referral_reward_paid = Column(Boolean, default=False, nullable=False)
    referral_code = Column(String(20), unique=True, nullable=False)

    # Wallet-specific details
    wallet_address = Column(String(100), nullable=True)  # For USDT (crypto address)
    bank_details_id = Column(UUID(), ForeignKey("bank_details.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="wallets")
    bank_details = relationship("BankDetails")
    wallet_logs = relationship("WalletLog", back_populates="wallet", cascade="all, delete-orphan")
    referral_rewards_given = relationship(
        "ReferralReward",
        foreign_keys="ReferralReward.referrer_wallet_id",
        back_populates="referrer_wallet"
    )
    referral_rewards_received = relationship(
        "ReferralReward",
        foreign_keys="ReferralReward.referred_wallet_id",
        back_populates="referred_wallet"
    )

    # Unique constraint: One wallet per currency per user
    __table_args__ = (
        UniqueConstraint('user_id', 'currency', name='_user_currency_uc'),
        Index('idx_wallet_user_currency', 'user_id', 'currency'),
        Index('idx_wallet_referral_code', 'referral_code'),
    )

    def __repr__(self):
        return f"<Wallet {self.currency.value} - {self.user.username if self.user else 'N/A'}>"


# ========================================
# BANK DETAILS
# ========================================

class BankDetails(Base):
    """Bank details for Naira wallets"""
    __tablename__ = "bank_details"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    account_number = Column(String(20), nullable=False)
    account_name = Column(String(255), nullable=False)
    bank_name = Column(String(100), nullable=False)
    bank_code = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<BankDetails {self.bank_name} - {self.account_number}>"


# ========================================
# WALLET LOG (Transaction History)
# ========================================

class WalletLog(Base):
    """Transaction history for wallets"""
    __tablename__ = "wallet_logs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(), ForeignKey("wallets.id"), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    type = Column(Enum(TransactionTypeEnum), nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    wallet = relationship("Wallet", back_populates="wallet_logs")

    __table_args__ = (
        Index('idx_wallet_log_wallet_created', 'wallet_id', 'created_at'),
    )

    def __repr__(self):
        return f"<WalletLog {self.type.value} {self.amount}>"


# ========================================
# REFERRAL REWARD
# ========================================

class ReferralReward(Base):
    """Track referral rewards paid"""
    __tablename__ = "referral_rewards"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    referrer_wallet_id = Column(UUID(), ForeignKey("wallets.id"), nullable=False)
    referred_wallet_id = Column(UUID(), ForeignKey("wallets.id"), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    referrer_wallet = relationship("Wallet", foreign_keys=[referrer_wallet_id], back_populates="referral_rewards_given")
    referred_wallet = relationship("Wallet", foreign_keys=[referred_wallet_id], back_populates="referral_rewards_received")

    def __repr__(self):
        return f"<ReferralReward {self.amount}>"


# ========================================
# FUNDING & WITHDRAWAL
# ========================================

class FundingRequest(Base):
    """P2P funding requests - Batch matching system"""
    __tablename__ = "funding_requests"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(), ForeignKey("wallets.id"), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    amount_remaining = Column(Numeric(18, 2), nullable=False)  # For partial matching
    is_fully_matched = Column(Boolean, default=False, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)  # All payments done
    opted_in = Column(Boolean, default=False, nullable=False)  # User joined the merge cycle
    opted_in_at = Column(DateTime, nullable=True)  # When user joined
    merge_cycle_id = Column(UUID(), nullable=True)  # Which merge cycle was this matched in
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    matched_at = Column(DateTime, nullable=True)

    # Legacy columns (for backward compatibility with old matching system)
    is_matched = Column(Boolean, default=False, nullable=False)
    sent = Column(Boolean, default=False, nullable=False)
    receipt_url = Column(String(500), nullable=True)
    match_time = Column(DateTime, nullable=True)
    matched_to_withdrawal_id = Column(UUID(), nullable=True)

    __table_args__ = (
        Index('idx_funding_wallet_match', 'wallet_id', 'is_fully_matched'),
    )

    def __repr__(self):
        return f"<FundingRequest {self.amount}>"


class WithdrawalRequest(Base):
    """P2P withdrawal requests - Batch matching system"""
    __tablename__ = "withdrawal_requests"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(), ForeignKey("wallets.id"), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    amount_remaining = Column(Numeric(18, 2), nullable=False)  # For partial matching
    is_fully_matched = Column(Boolean, default=False, nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)  # All payments done
    opted_in = Column(Boolean, default=False, nullable=False)  # User joined the merge cycle
    opted_in_at = Column(DateTime, nullable=True)  # When user joined
    merge_cycle_id = Column(UUID(), nullable=True)  # Which merge cycle was this matched in
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    matched_at = Column(DateTime, nullable=True)

    # Priority queue system for re-matching
    is_priority = Column(Boolean, default=False, nullable=False)  # Priority for next cycle
    priority_timestamp = Column(DateTime, nullable=True)  # Original join time for priority ordering
    failed_match_count = Column(Integer, default=0, nullable=False)  # How many times matched but funder failed

    # Legacy columns (for backward compatibility with old matching system)
    is_matched = Column(Boolean, default=False, nullable=False)
    matched_to_funder_id = Column(UUID(), nullable=True)
    match_time = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_withdrawal_wallet_match', 'wallet_id', 'is_fully_matched'),
    )

    def __repr__(self):
        return f"<WithdrawalRequest {self.amount}>"


class FundingMatchPair(Base):
    """Links funders to withdrawers - Supports many-to-many matching"""
    __tablename__ = "funding_match_pairs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    funding_request_id = Column(UUID(), ForeignKey("funding_requests.id"), nullable=False)
    withdrawal_request_id = Column(UUID(), ForeignKey("withdrawal_requests.id"), nullable=False)
    merge_cycle_id = Column(UUID(), ForeignKey("merge_cycles.id"), nullable=False)

    # Amount for this specific pair (can be partial)
    amount = Column(Numeric(18, 2), nullable=False)

    # Payment status
    proof_uploaded = Column(Boolean, default=False, nullable=False)
    proof_url = Column(String(500), nullable=True)
    proof_uploaded_at = Column(DateTime, nullable=True)
    proof_confirmed = Column(Boolean, default=False, nullable=False)
    proof_confirmed_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Deadlines (4 hours each)
    proof_deadline = Column(DateTime, nullable=True)  # Funder has 4 hours to upload proof
    confirmation_deadline = Column(DateTime, nullable=True)  # Withdrawer has 4 hours to confirm after proof uploaded

    # Extension support (1 hour max)
    extension_requested = Column(Boolean, default=False, nullable=False)
    extension_granted = Column(Boolean, default=False, nullable=False)
    extended_deadline = Column(DateTime, nullable=True)  # New deadline after 1-hour extension

    # Blocking flags
    funder_missed_deadline = Column(Boolean, default=False, nullable=False)
    withdrawer_missed_deadline = Column(Boolean, default=False, nullable=False)
    in_dispute = Column(Boolean, default=False, nullable=False)  # Admin needs to review
    dispute_reason = Column(String(500), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index('idx_match_pair_funding', 'funding_request_id'),
        Index('idx_match_pair_withdrawal', 'withdrawal_request_id'),
        Index('idx_match_pair_cycle', 'merge_cycle_id'),
    )

    def __repr__(self):
        return f"<FundingMatchPair amount={self.amount}>"


class MergeCycle(Base):
    """Tracks scheduled merge cycles (3x daily)"""
    __tablename__ = "merge_cycles"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    scheduled_time = Column(DateTime, nullable=False, unique=True, index=True)  # 9am, 3pm, 9pm
    cutoff_time = Column(DateTime, nullable=False)  # 1 hour before scheduled_time (for request creation)
    join_window_closes = Column(DateTime, nullable=True)  # 5 minutes after scheduled_time (when matching starts)
    status = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed

    # Stats
    total_funding_requests = Column(Integer, default=0, nullable=False)
    total_withdrawal_requests = Column(Integer, default=0, nullable=False)
    matched_pairs = Column(Integer, default=0, nullable=False)
    unmatched_funding = Column(Integer, default=0, nullable=False)
    unmatched_withdrawal = Column(Integer, default=0, nullable=False)
    admin_funded = Column(Integer, default=0, nullable=False)
    admin_withdrew = Column(Integer, default=0, nullable=False)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<MergeCycle {self.scheduled_time}>"


class AdminWallet(Base):
    """Admin wallets for liquidity provision"""
    __tablename__ = "admin_wallets"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    wallet_type = Column(String(20), nullable=False)  # funding_pool, platform_fees
    currency = Column(Enum(CurrencyEnum), nullable=False)
    balance = Column(Numeric(18, 2), default=0, nullable=False)

    # Tracking
    total_funded = Column(Numeric(18, 2), default=0, nullable=False)  # Total sent to users
    total_received = Column(Numeric(18, 2), default=0, nullable=False)  # Total received from users
    total_fees_collected = Column(Numeric(18, 2), default=0, nullable=False)  # For platform_fees wallet

    bank_account_number = Column(String(50), nullable=True)
    bank_name = Column(String(100), nullable=True)
    account_name = Column(String(100), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint('wallet_type', 'currency', name='uq_admin_wallet_type_currency'),
    )

    def __repr__(self):
        return f"<AdminWallet {self.wallet_type} {self.currency}>"


# ========================================
# BETTING MODELS (Shared across betting types)
# ========================================

class Game(Base):
    """Sports event for all betting types"""
    __tablename__ = "games"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    sport = Column(String(50), nullable=False)
    league = Column(String(100), nullable=True)

    scheduled_time = Column(DateTime, nullable=False, index=True)
    betting_closes_at = Column(DateTime, nullable=False)  # 1 hour before scheduled_time

    status = Column(String(20), default="upcoming", nullable=False)  # upcoming, live, finished, cancelled
    winner = Column(String(10), nullable=True)  # "home", "away", "draw"

    # Rendezvous group betting pools (cached for performance)
    home_total_naira = Column(Numeric(18, 2), default=0, nullable=False)
    away_total_naira = Column(Numeric(18, 2), default=0, nullable=False)
    home_total_usdt = Column(Numeric(18, 2), default=0, nullable=False)
    away_total_usdt = Column(Numeric(18, 2), default=0, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    result_set_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_game_status_scheduled', 'status', 'scheduled_time'),
    )

    def __repr__(self):
        return f"<Game {self.home_team} vs {self.away_team}>"


class BetTypeEnum(str, enum.Enum):
    """Types of bets"""
    RENDEZVOUS = "rendezvous"  # Group betting
    ONE_V_ONE = "1v1"           # Peer-to-peer matched
    CUSTOM = "custom"           # User-created


class BetSideEnum(str, enum.Enum):
    """Betting sides"""
    HOME = "home"
    AWAY = "away"


class BetRegistration(Base):
    """All bet registrations (Rendezvous and 1v1)"""
    __tablename__ = "bet_registrations"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(), ForeignKey("wallets.id"), nullable=False)
    game_id = Column(UUID(), ForeignKey("games.id"), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    side = Column(Enum(BetSideEnum), nullable=False)
    bet_type = Column(Enum(BetTypeEnum), nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, won, lost, refunded

    # Payout info (calculated after game ends)
    payout = Column(Numeric(18, 2), default=0, nullable=False)
    profit = Column(Numeric(18, 2), default=0, nullable=False)
    share_percentage = Column(Numeric(5, 4), default=0, nullable=True)  # For Rendezvous only

    # Match pair reference (for 1v1 only)
    match_pair_id = Column(UUID(), ForeignKey("match_pairs.id"), nullable=True)

    registered_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    settled_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_bet_wallet_game', 'wallet_id', 'game_id'),
        Index('idx_bet_game_type_status', 'game_id', 'bet_type', 'status'),
    )

    def __repr__(self):
        return f"<BetRegistration {self.bet_type.value} {self.amount}>"


# ========================================
# 1v1 BETTING MODELS
# ========================================

class BetQueue(Base):
    """Queue for users waiting for 1v1 match"""
    __tablename__ = "bet_queue"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    wallet_id = Column(UUID(), ForeignKey("wallets.id"), nullable=False)
    game_id = Column(UUID(), ForeignKey("games.id"), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    side = Column(Enum(BetSideEnum), nullable=False)
    currency = Column(Enum(CurrencyEnum), nullable=False)
    status = Column(String(20), default="waiting", nullable=False)  # waiting, matched, expired, cancelled

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # 1 hour before game starts

    __table_args__ = (
        Index('idx_queue_game_amount_side', 'game_id', 'amount', 'side', 'currency', 'status'),
    )

    def __repr__(self):
        return f"<BetQueue {self.amount} {self.side.value}>"


class MatchPair(Base):
    """Matched 1v1 bet pair"""
    __tablename__ = "match_pairs"

    id = Column(UUID(), primary_key=True, default=uuid.uuid4)
    game_id = Column(UUID(), ForeignKey("games.id"), nullable=False)

    # Both users
    wallet_a_id = Column(UUID(), ForeignKey("wallets.id"), nullable=False)
    wallet_b_id = Column(UUID(), ForeignKey("wallets.id"), nullable=False)

    # Bet references
    bet_a_id = Column(UUID(), ForeignKey("bet_registrations.id"), nullable=False)
    bet_b_id = Column(UUID(), ForeignKey("bet_registrations.id"), nullable=False)

    # Match details
    amount = Column(Numeric(18, 2), nullable=False)  # Same for both
    currency = Column(Enum(CurrencyEnum), nullable=False)
    status = Column(String(20), default="matched", nullable=False)  # matched, settled, refunded

    # Result
    winner_wallet_id = Column(UUID(), nullable=True)
    payout = Column(Numeric(18, 2), default=0, nullable=False)
    platform_fee = Column(Numeric(18, 2), default=0, nullable=False)

    matched_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    settled_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index('idx_match_game_status', 'game_id', 'status'),
    )

    def __repr__(self):
        return f"<MatchPair {self.amount}>"


# Additional models (CustomBet, etc.) will be added in their respective service folders

# This shared file contains core models used across all services
