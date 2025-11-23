"""
Funding Service - 2-Aside Platform
BATCH MATCHING SYSTEM - 3 Merge Cycles Daily
Smart amount splitting with admin wallet fallback
"""

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
import sys
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict
import pytz
import shutil
from pathlib import Path
import logging

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared import (
    get_db,
    User,
    Wallet,
    BankDetails,
    FundingRequest,
    WithdrawalRequest,
    FundingMatchPair,
    MergeCycle,
    AdminWallet,
    WalletLog,
    SuccessResponse,
    PaginatedResponse,
    PaginationMeta,
    get_current_user_id,
    WalletNotFoundError,
    InsufficientBalanceError,
    InvalidAmountError,
    TwoAsideBaseException,
)

# Import simplified merge scheduler
from merge_scheduler import (
    get_next_merge_time,
    format_next_merge_time,
    is_within_join_window,
    get_current_merge_window_info
)

# Import auto matcher
from auto_matcher import get_scheduler

# Initialize FastAPI app
app = FastAPI(
    title="2-Aside Funding Service",
    description="P2P Batch Matching System with 3 Daily Merge Cycles",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ========================================
# STARTUP EVENT - Start Auto-Matching Scheduler
# ========================================

@app.on_event("startup")
async def startup_event():
    """Start the automatic matching scheduler on app startup."""
    # Start auto-matching scheduler
    scheduler = get_scheduler()
    print("[OK] Auto-matching scheduler started")
    print("[INFO] Matching will run automatically at 9am, 3pm, 9pm WAT")

    # Start blob cleanup scheduler
    from blob_cleanup_task import get_cleanup_scheduler
    cleanup_scheduler = get_cleanup_scheduler()
    print("[OK] Blob cleanup scheduler started")

    # Create uploads directory for fallback (if Azure not configured)
    uploads_dir = Path("uploads/payment_proofs")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    print(f"[OK] Uploads directory ready: {uploads_dir.absolute()}")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded payment proofs
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Constants
MERGE_CYCLE_TIMES = [9, 15, 21]  # 9 AM, 3 PM, 9 PM
CUTOFF_MINUTES_BEFORE_MERGE = 10  # Users can cancel up to 10 minutes before merge
MIN_AMOUNT = Decimal("1000")
MAX_AMOUNT = Decimal("10000000")


# ========================================
# HEALTH CHECK
# ========================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "funding-service-v2-batch-matching"}


# ========================================
# HELPER FUNCTIONS
# ========================================

def get_next_merge_cycle(db: Session) -> Optional[MergeCycle]:
    """Get the next scheduled merge cycle"""
    now = datetime.utcnow()
    cycle = db.query(MergeCycle).filter(
        MergeCycle.scheduled_time > now,
        MergeCycle.status == "pending"
    ).order_by(MergeCycle.scheduled_time).first()
    return cycle


def is_before_cutoff(merge_cycle: MergeCycle) -> bool:
    """Check if current time is before the cutoff time"""
    now = datetime.utcnow()
    return now < merge_cycle.cutoff_time


def has_pending_request(user_id: uuid.UUID, db: Session) -> Dict[str, bool]:
    """Check if user has any pending requests"""
    funding = db.query(FundingRequest).filter(
        FundingRequest.wallet_id.in_(
            db.query(Wallet.id).filter(Wallet.user_id == user_id)
        ),
        FundingRequest.is_completed == False
    ).first()

    withdrawal = db.query(WithdrawalRequest).filter(
        WithdrawalRequest.wallet_id.in_(
            db.query(Wallet.id).filter(Wallet.user_id == user_id)
        ),
        WithdrawalRequest.is_completed == False
    ).first()

    return {
        "has_pending_funding": funding is not None,
        "has_pending_withdrawal": withdrawal is not None,
        "has_any_pending": funding is not None or withdrawal is not None
    }


# ========================================
# CREATE FUNDING REQUEST
# ========================================

@app.post(
    "/funding/request",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Funding"]
)
async def create_funding_request(
    amount: Decimal = Query(..., description="Amount to fund"),
    currency: str = Query(..., description="NAIRA or USDT"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a funding request (deposit).
    Will be matched in the next merge cycle (3x daily: 9 AM, 3 PM, 9 PM WAT).
    Cannot create if you have a pending funding or withdrawal request.
    """
    try:
        # Validate amount
        if amount < MIN_AMOUNT:
            raise InvalidAmountError(f"Minimum funding amount is {MIN_AMOUNT}", minimum=float(MIN_AMOUNT))
        if amount > MAX_AMOUNT:
            raise InvalidAmountError(f"Maximum funding amount is {MAX_AMOUNT}", maximum=float(MAX_AMOUNT))

        # Validate currency
        if currency.upper() not in ["NAIRA", "USDT"]:
            raise HTTPException(status_code=400, detail="Currency must be NAIRA or USDT")

        currency_upper = currency.upper()

        # Check for pending requests
        pending = has_pending_request(uuid.UUID(user_id), db)
        if pending["has_any_pending"]:
            raise HTTPException(
                status_code=400,
                detail="You already have a pending request. Complete or cancel it before creating a new one."
            )

        # Get next merge time using real-time WAT checking (no database query needed)
        next_merge_utc, join_window_closes_utc = get_next_merge_time()
        next_merge_formatted = format_next_merge_time()

        # Note: Users can create requests anytime. They will be matched at the next merge time.
        # Merge times are 9am, 3pm, 9pm WAT (West Africa Time) daily.

        # Get wallet
        wallet = db.query(Wallet).filter(
            Wallet.user_id == uuid.UUID(user_id),
            Wallet.currency == currency_upper
        ).first()

        if not wallet:
            raise WalletNotFoundError()

        # Check if wallet is blocked
        if wallet.is_blocked:
            raise HTTPException(
                status_code=403,
                detail=f"Your account is blocked. Reason: {wallet.block_reason or 'Contact support for more information.'}"
            )

        # Check if user has set bank account (NAIRA) or wallet address (USDT)
        if currency_upper == "NAIRA":
            if not wallet.bank_details_id:
                raise HTTPException(
                    status_code=400,
                    detail="You must set your bank account before creating a funding request. Go to Wallet settings to add your bank account. IMPORTANT: Ensure the account name matches your registered name."
                )
        elif currency_upper == "USDT":
            if not wallet.wallet_address:
                raise HTTPException(
                    status_code=400,
                    detail="You must set your BEP20 USDT wallet address before creating a funding request. Go to Wallet settings to add your wallet address. WARNING: This cannot be changed once set."
                )

        # Create funding request
        funding_request = FundingRequest(
            id=uuid.uuid4(),
            wallet_id=wallet.id,
            amount=amount,
            amount_remaining=amount,
            is_fully_matched=False,
            is_completed=False,
            requested_at=datetime.utcnow()
        )

        db.add(funding_request)
        db.commit()
        db.refresh(funding_request)

        return SuccessResponse(
            message=f"Funding request created. Will be matched at {next_merge_formatted}",
            data={
                "request_id": str(funding_request.id),
                "amount": str(funding_request.amount),
                "currency": currency_upper,
                "status": "pending",
                "next_merge_time": next_merge_utc.isoformat(),
                "join_window_closes": join_window_closes_utc.isoformat()
            }
        )

    except TwoAsideBaseException as e:
        db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "detail": str(e)})


# ========================================
# CREATE WITHDRAWAL REQUEST
# ========================================

@app.post(
    "/withdrawal/request",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Withdrawal"]
)
async def create_withdrawal_request(
    amount: Decimal = Query(..., description="Amount to withdraw"),
    currency: str = Query(..., description="NAIRA or USDT"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Create a withdrawal request.
    Will be matched in the next merge cycle (3x daily: 9 AM, 3 PM, 9 PM WAT).
    Cannot create if you have a pending funding or withdrawal request.
    """
    try:
        # Validate amount
        if amount < MIN_AMOUNT:
            raise InvalidAmountError(f"Minimum withdrawal amount is {MIN_AMOUNT}", minimum=float(MIN_AMOUNT))
        if amount > MAX_AMOUNT:
            raise InvalidAmountError(f"Maximum withdrawal amount is {MAX_AMOUNT}", maximum=float(MAX_AMOUNT))

        # Validate currency
        if currency.upper() not in ["NAIRA", "USDT"]:
            raise HTTPException(status_code=400, detail="Currency must be NAIRA or USDT")

        currency_upper = currency.upper()

        # Check for pending requests
        pending = has_pending_request(uuid.UUID(user_id), db)
        if pending["has_any_pending"]:
            raise HTTPException(
                status_code=400,
                detail="You already have a pending request. Complete or cancel it before creating a new one."
            )

        # Get next merge time using real-time WAT checking (no database query needed)
        next_merge_utc, join_window_closes_utc = get_next_merge_time()
        next_merge_formatted = format_next_merge_time()

        # Note: Users can create requests anytime. They will be matched at the next merge time.
        # Merge times are 9am, 3pm, 9pm WAT (West Africa Time) daily.

        # Get wallet
        wallet = db.query(Wallet).filter(
            Wallet.user_id == uuid.UUID(user_id),
            Wallet.currency == currency_upper
        ).first()

        if not wallet:
            raise WalletNotFoundError()

        # Check if wallet is blocked
        if wallet.is_blocked:
            raise HTTPException(
                status_code=403,
                detail=f"Your account is blocked. Reason: {wallet.block_reason or 'Contact support for more information.'}"
            )

        # Check if user has set bank account (NAIRA) or wallet address (USDT)
        if currency_upper == "NAIRA":
            if not wallet.bank_details_id:
                raise HTTPException(
                    status_code=400,
                    detail="You must set your bank account before creating a withdrawal request. Go to Wallet settings to add your bank account. IMPORTANT: Ensure the account name matches your registered name."
                )
        elif currency_upper == "USDT":
            if not wallet.wallet_address:
                raise HTTPException(
                    status_code=400,
                    detail="You must set your BEP20 USDT wallet address before creating a withdrawal request. Go to Wallet settings to add your wallet address. WARNING: This cannot be changed once set."
                )

        # Check balance
        if wallet.balance < amount:
            raise InsufficientBalanceError(required=float(amount), available=float(wallet.balance))

        # Create withdrawal request
        withdrawal_request = WithdrawalRequest(
            id=uuid.uuid4(),
            wallet_id=wallet.id,
            amount=amount,
            amount_remaining=amount,
            is_fully_matched=False,
            is_completed=False,
            requested_at=datetime.utcnow()
        )

        db.add(withdrawal_request)
        db.commit()
        db.refresh(withdrawal_request)

        return SuccessResponse(
            message=f"Withdrawal request created. Will be matched at {next_merge_formatted}",
            data={
                "request_id": str(withdrawal_request.id),
                "amount": str(withdrawal_request.amount),
                "currency": currency_upper,
                "status": "pending",
                "next_merge_time": next_merge_utc.isoformat(),
                "join_window_closes": join_window_closes_utc.isoformat()
            }
        )

    except TwoAsideBaseException as e:
        db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": "Internal server error", "detail": str(e)})


# ========================================
# GET MY REQUESTS
# ========================================

@app.get("/funding/my-requests", tags=["Funding"])
async def get_my_funding_requests(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get my funding requests with match details"""
    try:
        # Get user's wallets
        wallets = db.query(Wallet).filter(Wallet.user_id == uuid.UUID(user_id)).all()
        wallet_ids = [w.id for w in wallets]

        # Get funding requests
        requests = db.query(FundingRequest).filter(
            FundingRequest.wallet_id.in_(wallet_ids)
        ).order_by(desc(FundingRequest.requested_at)).all()

        data = []
        for req in requests:
            # Get matched pairs
            pairs = db.query(FundingMatchPair).filter(
                FundingMatchPair.funding_request_id == req.id
            ).all()

            matched_users = []
            for pair in pairs:
                withdrawal = db.query(WithdrawalRequest).filter(
                    WithdrawalRequest.id == pair.withdrawal_request_id
                ).first()
                if withdrawal:
                    withdrawer_wallet = db.query(Wallet).filter(Wallet.id == withdrawal.wallet_id).first()
                    if withdrawer_wallet:
                        withdrawer_user = db.query(User).filter(User.id == withdrawer_wallet.user_id).first()
                        if withdrawer_user:
                            matched_users.append({
                                "username": withdrawer_user.username,
                                "phone": withdrawer_user.phone,
                                "amount": str(pair.amount),
                                "proof_uploaded": pair.proof_uploaded,
                                "proof_confirmed": pair.proof_confirmed,
                                "pair_id": str(pair.id)
                            })

            wallet = db.query(Wallet).filter(Wallet.id == req.wallet_id).first()

            data.append({
                "id": str(req.id),
                "amount": str(req.amount),
                "amount_remaining": str(req.amount_remaining),
                "currency": wallet.currency if wallet else "UNKNOWN",
                "is_fully_matched": req.is_fully_matched,
                "is_completed": req.is_completed,
                "matched_users": matched_users,
                "requested_at": req.requested_at.isoformat(),
                "matched_at": req.matched_at.isoformat() if req.matched_at else None
            })

        return SuccessResponse(message="Funding requests retrieved", data=data)

    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.get("/withdrawal/my-requests", tags=["Withdrawal"])
async def get_my_withdrawal_requests(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get my withdrawal requests with match details"""
    try:
        # Get user's wallets
        wallets = db.query(Wallet).filter(Wallet.user_id == uuid.UUID(user_id)).all()
        wallet_ids = [w.id for w in wallets]

        # Get withdrawal requests
        requests = db.query(WithdrawalRequest).filter(
            WithdrawalRequest.wallet_id.in_(wallet_ids)
        ).order_by(desc(WithdrawalRequest.requested_at)).all()

        data = []
        for req in requests:
            # Get matched pairs
            pairs = db.query(FundingMatchPair).filter(
                FundingMatchPair.withdrawal_request_id == req.id
            ).all()

            matched_users = []
            for pair in pairs:
                funding = db.query(FundingRequest).filter(
                    FundingRequest.id == pair.funding_request_id
                ).first()
                if funding:
                    funder_wallet = db.query(Wallet).filter(Wallet.id == funding.wallet_id).first()
                    if funder_wallet:
                        funder_user = db.query(User).filter(User.id == funder_wallet.user_id).first()
                        if funder_user:
                            matched_users.append({
                                "username": funder_user.username,
                                "phone": funder_user.phone,
                                "amount": str(pair.amount),
                                "proof_uploaded": pair.proof_uploaded,
                                "proof_confirmed": pair.proof_confirmed,
                                "pair_id": str(pair.id)
                            })

            wallet = db.query(Wallet).filter(Wallet.id == req.wallet_id).first()

            data.append({
                "id": str(req.id),
                "amount": str(req.amount),
                "amount_remaining": str(req.amount_remaining),
                "currency": wallet.currency if wallet else "UNKNOWN",
                "is_fully_matched": req.is_fully_matched,
                "is_completed": req.is_completed,
                "matched_users": matched_users,
                "requested_at": req.requested_at.isoformat(),
                "matched_at": req.matched_at.isoformat() if req.matched_at else None
            })

        return SuccessResponse(message="Withdrawal requests retrieved", data=data)

    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


# ========================================
# CANCEL REQUESTS
# ========================================

@app.delete("/funding/request/{request_id}/cancel", tags=["Funding"])
async def cancel_funding_request(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Cancel a funding request.
    Can only cancel if:
    - Request is not yet matched
    - Current time is more than 10 minutes before next merge cycle
    """
    try:
        # Get the funding request
        funding_req = db.query(FundingRequest).filter(
            FundingRequest.id == uuid.UUID(request_id)
        ).first()

        if not funding_req:
            raise HTTPException(status_code=404, detail="Funding request not found")

        # Verify ownership
        wallet = db.query(Wallet).filter(Wallet.id == funding_req.wallet_id).first()
        if str(wallet.user_id) != user_id:
            raise HTTPException(status_code=403, detail="You can only cancel your own requests")

        # Check if already completed
        if funding_req.is_completed:
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel a completed request"
            )

        # Check if already matched
        if funding_req.is_fully_matched or funding_req.matched_at:
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel a request that has already been matched. Please complete the transaction or contact admin."
            )

        # Get next merge cycle
        next_cycle = get_next_merge_cycle(db)
        if not next_cycle:
            # No next cycle, safe to cancel
            pass
        else:
            # Check if we're within 10 minutes of merge (cutoff time)
            if not is_before_cutoff(next_cycle):
                time_until_merge = (next_cycle.scheduled_time - datetime.utcnow()).total_seconds() / 60
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel within 10 minutes of merge cycle. Next merge is in {int(time_until_merge)} minutes. Please wait until after the merge to cancel."
                )

        # Delete the request
        db.delete(funding_req)
        db.commit()

        return SuccessResponse(
            message="Funding request cancelled successfully",
            data={
                "request_id": str(funding_req.id),
                "amount": str(funding_req.amount),
                "cancelled_at": datetime.utcnow().isoformat()
            }
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.delete("/withdrawal/request/{request_id}/cancel", tags=["Withdrawal"])
async def cancel_withdrawal_request(
    request_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Cancel a withdrawal request.
    Can only cancel if:
    - Request is not yet matched
    - Current time is more than 10 minutes before next merge cycle
    """
    try:
        # Get the withdrawal request
        withdrawal_req = db.query(WithdrawalRequest).filter(
            WithdrawalRequest.id == uuid.UUID(request_id)
        ).first()

        if not withdrawal_req:
            raise HTTPException(status_code=404, detail="Withdrawal request not found")

        # Verify ownership
        wallet = db.query(Wallet).filter(Wallet.id == withdrawal_req.wallet_id).first()
        if str(wallet.user_id) != user_id:
            raise HTTPException(status_code=403, detail="You can only cancel your own requests")

        # Check if already completed
        if withdrawal_req.is_completed:
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel a completed request"
            )

        # Check if already matched
        if withdrawal_req.is_fully_matched or withdrawal_req.matched_at:
            raise HTTPException(
                status_code=400,
                detail="Cannot cancel a request that has already been matched. Please complete the transaction or contact admin."
            )

        # Get next merge cycle
        next_cycle = get_next_merge_cycle(db)
        if not next_cycle:
            # No next cycle, safe to cancel
            pass
        else:
            # Check if we're within 10 minutes of merge (cutoff time)
            if not is_before_cutoff(next_cycle):
                time_until_merge = (next_cycle.scheduled_time - datetime.utcnow()).total_seconds() / 60
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot cancel within 10 minutes of merge cycle. Next merge is in {int(time_until_merge)} minutes. Please wait until after the merge to cancel."
                )

        # Delete the request
        db.delete(withdrawal_req)
        db.commit()

        return SuccessResponse(
            message="Withdrawal request cancelled successfully",
            data={
                "request_id": str(withdrawal_req.id),
                "amount": str(withdrawal_req.amount),
                "cancelled_at": datetime.utcnow().isoformat()
            }
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e)})


# ========================================
# GET NEXT MERGE CYCLE INFO
# ========================================

@app.get("/merge-cycle/next", tags=["Merge Cycle"])
async def get_next_merge_cycle_info():
    """Get information about the next merge cycle using real-time WAT checking (no database needed)"""
    try:
        # Use simplified scheduler - no database query needed
        next_merge_utc, join_window_closes_utc = get_next_merge_time()
        next_merge_formatted = format_next_merge_time()
        current_window_info = get_current_merge_window_info()

        now = datetime.utcnow()
        time_until_merge = (next_merge_utc - now).total_seconds()

        # Ensure UTC datetimes have timezone info for proper conversion
        merge_time_utc_aware = pytz.utc.localize(next_merge_utc) if next_merge_utc.tzinfo is None else next_merge_utc
        join_window_utc_aware = pytz.utc.localize(join_window_closes_utc) if join_window_closes_utc.tzinfo is None else join_window_closes_utc

        return SuccessResponse(
            message="Next merge cycle info",
            data={
                "has_cycle": True,
                "merge_time": merge_time_utc_aware.isoformat(),  # ISO format with timezone
                "merge_time_formatted": next_merge_formatted,
                "join_window_closes": join_window_utc_aware.isoformat(),  # ISO format with timezone
                "can_create_request": True,  # Users can always create requests
                "time_until_merge_seconds": int(time_until_merge),
                "is_join_window_open": current_window_info is not None,
                "current_window": current_window_info
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.post("/merge-cycle/join", tags=["Merge Cycle"], status_code=status.HTTP_200_OK)
async def join_merge_cycle(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Join the current merge cycle window.
    Only users with pending requests can join.
    This opts them in for matching during the current cycle.
    Uses real-time WAT checking - no database merge cycles needed.
    """
    try:
        user_uuid = uuid.UUID(user_id)

        # Check if we're within the 5-minute join window using real-time checking
        window_info = get_current_merge_window_info()

        if not window_info:
            # Not in a join window - tell user when next one is
            next_merge_formatted = format_next_merge_time()
            next_merge_utc, _ = get_next_merge_time()
            now = datetime.utcnow()
            minutes_until_window = int((next_merge_utc - now).total_seconds() / 60)

            raise HTTPException(
                status_code=400,
                detail=f"Join window is not open. Next window opens at {next_merge_formatted} (in {minutes_until_window} minutes)"
            )

        # Find user's pending requests
        funding_req = db.query(FundingRequest).join(Wallet).filter(
            Wallet.user_id == user_uuid,
            FundingRequest.is_completed == False,
            FundingRequest.opted_in == False
        ).first()

        withdrawal_req = db.query(WithdrawalRequest).join(Wallet).filter(
            Wallet.user_id == user_uuid,
            WithdrawalRequest.is_completed == False,
            WithdrawalRequest.opted_in == False
        ).first()

        if not funding_req and not withdrawal_req:
            raise HTTPException(
                status_code=400,
                detail="No pending requests found or you have already joined this cycle"
            )

        # Mark as opted in
        request_type = ""
        if funding_req:
            funding_req.opted_in = True
            funding_req.opted_in_at = now
            request_type = "funding"

        if withdrawal_req:
            withdrawal_req.opted_in = True
            withdrawal_req.opted_in_at = now
            request_type = "withdrawal"

        db.commit()

        return SuccessResponse(
            message=f"Successfully joined merge cycle! You will be matched with other users shortly.",
            data={
                "request_type": request_type,
                "cycle_time": window_info['merge_time_utc'].isoformat(),
                "cycle_time_wat": window_info['merge_time_wat'],
                "window_closes": window_info['window_closes_wat'],
                "seconds_remaining": window_info['seconds_remaining'],
                "opted_in_at": now.isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.get("/merge-cycle/my-status", tags=["Merge Cycle"])
async def get_my_merge_cycle_status(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Check if user has pending requests and if they can join the merge cycle.
    Uses real-time WAT checking - no database merge cycles needed.
    """
    try:
        user_uuid = uuid.UUID(user_id)

        # Get merge window info using real-time checking
        window_info = get_current_merge_window_info()
        next_merge_formatted = format_next_merge_time()
        next_merge_utc, join_window_closes_utc = get_next_merge_time()

        # Check for pending requests
        funding_req = db.query(FundingRequest).join(Wallet).filter(
            Wallet.user_id == user_uuid,
            FundingRequest.is_completed == False
        ).first()

        withdrawal_req = db.query(WithdrawalRequest).join(Wallet).filter(
            Wallet.user_id == user_uuid,
            WithdrawalRequest.is_completed == False
        ).first()

        has_pending = funding_req is not None or withdrawal_req is not None
        already_opted_in = (funding_req and funding_req.opted_in) or (withdrawal_req and withdrawal_req.opted_in)

        # Check if within the 5-minute join window using real-time checking
        in_join_window = window_info is not None
        can_join = has_pending and not already_opted_in and in_join_window

        return SuccessResponse(
            message="Merge cycle status",
            data={
                "has_cycle": True,
                "next_merge_time": next_merge_utc.isoformat(),
                "next_merge_formatted": next_merge_formatted,
                "join_window_closes": join_window_closes_utc.isoformat(),
                "has_pending_request": has_pending,
                "already_opted_in": already_opted_in,
                "in_join_window": in_join_window,
                "window_info": window_info,
                "can_join": can_join,
                "request_type": "funding" if funding_req else ("withdrawal" if withdrawal_req else None)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.get("/my-active-matches", tags=["Merge Cycle"])
async def get_my_active_matches(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get user's active match pairs that require action (payment or confirmation)
    """
    try:
        user_uuid = uuid.UUID(user_id)

        # Get all match pairs where user is either funder or withdrawer
        # and the pair is not yet completed

        # User as funder (needs to pay)
        funder_pairs = db.query(FundingMatchPair).join(
            FundingRequest, FundingMatchPair.funding_request_id == FundingRequest.id
        ).join(
            Wallet, FundingRequest.wallet_id == Wallet.id
        ).filter(
            Wallet.user_id == user_uuid,
            FundingMatchPair.proof_confirmed == False
        ).all()

        # User as withdrawer (needs to confirm payment)
        withdrawer_pairs = db.query(FundingMatchPair).join(
            WithdrawalRequest, FundingMatchPair.withdrawal_request_id == WithdrawalRequest.id
        ).join(
            Wallet, WithdrawalRequest.wallet_id == Wallet.id
        ).filter(
            Wallet.user_id == user_uuid,
            FundingMatchPair.proof_confirmed == False
        ).all()

        # Format funder pairs (user needs to upload proof)
        funder_match_data = []
        for pair in funder_pairs:
            withdrawal_req = db.query(WithdrawalRequest).filter(
                WithdrawalRequest.id == pair.withdrawal_request_id
            ).first()
            withdrawer_wallet = db.query(Wallet).filter(Wallet.id == withdrawal_req.wallet_id).first()
            withdrawer_user = db.query(User).filter(User.id == withdrawer_wallet.user_id).first()

            # Get payment details
            payment_details = {}
            if withdrawer_wallet.currency == "NAIRA" and withdrawer_wallet.bank_details_id:
                bank_details = db.query(BankDetails).filter(
                    BankDetails.id == withdrawer_wallet.bank_details_id
                ).first()
                if bank_details:
                    payment_details = {
                        "type": "bank",
                        "account_number": bank_details.account_number,
                        "account_name": bank_details.account_name,
                        "bank_name": bank_details.bank_name
                    }
            elif withdrawer_wallet.currency == "USDT":
                payment_details = {
                    "type": "crypto",
                    "wallet_address": withdrawer_wallet.wallet_address,
                    "network": "BEP20"
                }

            now = datetime.utcnow()
            deadline = pair.extended_deadline if pair.extension_granted else pair.proof_deadline
            time_remaining_seconds = (deadline - now).total_seconds() if deadline else None

            funder_match_data.append({
                "pair_id": str(pair.id),
                "role": "funder",
                "amount": str(pair.amount),
                "currency": withdrawer_wallet.currency,
                "matched_user": {
                    "username": withdrawer_user.username,
                    "phone": withdrawer_user.phone,
                    "payment_details": payment_details
                },
                "proof_uploaded": pair.proof_uploaded,
                "proof_url": pair.proof_url,
                "proof_deadline": deadline.isoformat() if deadline else None,
                "time_remaining_seconds": int(time_remaining_seconds) if time_remaining_seconds else None,
                "can_extend": not pair.extension_requested and pair.proof_uploaded == False,
                "extension_requested": pair.extension_requested,
                "created_at": pair.created_at.isoformat()
            })

        # Format withdrawer pairs (user needs to confirm payment)
        withdrawer_match_data = []
        for pair in withdrawer_pairs:
            funding_req = db.query(FundingRequest).filter(
                FundingRequest.id == pair.funding_request_id
            ).first()
            funder_wallet = db.query(Wallet).filter(Wallet.id == funding_req.wallet_id).first()
            funder_user = db.query(User).filter(User.id == funder_wallet.user_id).first()

            now = datetime.utcnow()
            time_remaining_seconds = (pair.confirmation_deadline - now).total_seconds() if pair.confirmation_deadline else None

            withdrawer_match_data.append({
                "pair_id": str(pair.id),
                "role": "withdrawer",
                "amount": str(pair.amount),
                "currency": funder_wallet.currency,
                "matched_user": {
                    "username": funder_user.username,
                    "phone": funder_user.phone
                },
                "proof_uploaded": pair.proof_uploaded,
                "proof_url": pair.proof_url,
                "proof_confirmed": pair.proof_confirmed,
                "confirmation_deadline": pair.confirmation_deadline.isoformat() if pair.confirmation_deadline else None,
                "time_remaining_seconds": int(time_remaining_seconds) if time_remaining_seconds else None,
                "awaiting_proof": not pair.proof_uploaded,
                "awaiting_confirmation": pair.proof_uploaded and not pair.proof_confirmed,
                "created_at": pair.created_at.isoformat()
            })

        return SuccessResponse(
            message="Active matches retrieved successfully",
            data={
                "as_funder": funder_match_data,
                "as_withdrawer": withdrawer_match_data,
                "total_active": len(funder_match_data) + len(withdrawer_match_data)
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


# ========================================
# PROOF UPLOAD & CONFIRMATION
# ========================================

@app.post("/match-pair/{pair_id}/upload-proof", tags=["Proof"])
async def upload_proof(
    pair_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Upload proof of payment image for a match pair (funder only)"""
    try:
        pair = db.query(FundingMatchPair).filter(FundingMatchPair.id == uuid.UUID(pair_id)).first()
        if not pair:
            raise HTTPException(status_code=404, detail="Match pair not found")

        # Verify user is the funder
        funding_req = db.query(FundingRequest).filter(FundingRequest.id == pair.funding_request_id).first()
        if not funding_req:
            raise HTTPException(status_code=404, detail="Funding request not found")

        wallet = db.query(Wallet).filter(Wallet.id == funding_req.wallet_id).first()
        if str(wallet.user_id) != user_id:
            raise HTTPException(status_code=403, detail="You can only upload proof for your own matches")

        if pair.proof_uploaded:
            raise HTTPException(status_code=400, detail="Proof already uploaded")

        # Check if proof deadline has passed
        now = datetime.utcnow()
        if pair.proof_deadline and now > pair.proof_deadline:
            # Block the funder's wallet
            wallet.is_blocked = True
            wallet.block_reason = "Failed to upload payment proof within 4 hours. Please contact support at support@2aside.com to resolve this issue and unblock your account."

            # Get the withdrawal request to re-queue it with priority
            withdrawal_req = db.query(WithdrawalRequest).filter(
                WithdrawalRequest.id == pair.withdrawal_request_id
            ).first()

            if withdrawal_req:
                # Mark as priority for next merge cycle
                withdrawal_req.is_priority = True
                withdrawal_req.priority_timestamp = withdrawal_req.opted_in_at or withdrawal_req.requested_at
                withdrawal_req.failed_match_count += 1

                # Reset the withdrawal request to be available for next cycle
                withdrawal_req.is_fully_matched = False
                withdrawal_req.opted_in = False
                withdrawal_req.merge_cycle_id = None
                withdrawal_req.matched_at = None

                # Restore the amount that was matched
                withdrawal_req.amount_remaining += pair.amount

            # Mark the pair as failed
            pair.funder_missed_deadline = True

            db.commit()

            raise HTTPException(
                status_code=400,
                detail="Proof upload deadline has passed (4 hours). Your account has been blocked. Please contact support at support@2aside.com to unblock your account."
            )

        # Validate file type
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
            )

        # Read file content
        file_content = await file.read()

        # Try to upload to Azure Blob Storage first
        proof_url = None
        try:
            from azure_blob_service import azure_blob_service
            content_type = file.content_type or "application/octet-stream"
            proof_url = azure_blob_service.upload_file(file_content, file.filename, content_type)
            logger.info(f"Uploaded proof to Azure Blob Storage: {proof_url}")
        except Exception as azure_error:
            # Fallback to local storage if Azure fails
            logger.warning(f"Azure upload failed, using local storage: {azure_error}")
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = Path("uploads/payment_proofs") / unique_filename

            # Save file locally
            with file_path.open("wb") as buffer:
                buffer.write(file_content)

            proof_url = f"/uploads/payment_proofs/{unique_filename}"
            logger.info(f"Uploaded proof to local storage: {proof_url}")

        # Update database
        pair.proof_uploaded = True
        pair.proof_url = proof_url
        pair.proof_uploaded_at = now
        pair.confirmation_deadline = now + timedelta(hours=4)  # Withdrawer has 4 hours to confirm
        db.commit()

        return SuccessResponse(
            message="Proof uploaded successfully. Waiting for confirmation (withdrawer has 4 hours)...",
            data={
                "pair_id": str(pair.id),
                "proof_url": proof_url,
                "confirmation_deadline": pair.confirmation_deadline.isoformat()
            }
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.post("/match-pair/{pair_id}/confirm-proof", tags=["Proof"])
async def confirm_proof(
    pair_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Confirm receipt of payment for a match pair (withdrawer only)"""
    try:
        pair = db.query(FundingMatchPair).filter(FundingMatchPair.id == uuid.UUID(pair_id)).first()
        if not pair:
            raise HTTPException(status_code=404, detail="Match pair not found")

        # Verify user is the withdrawer
        withdrawal_req = db.query(WithdrawalRequest).filter(
            WithdrawalRequest.id == pair.withdrawal_request_id
        ).first()
        if not withdrawal_req:
            raise HTTPException(status_code=404, detail="Withdrawal request not found")

        wallet = db.query(Wallet).filter(Wallet.id == withdrawal_req.wallet_id).first()
        if str(wallet.user_id) != user_id:
            raise HTTPException(status_code=403, detail="You can only confirm proof for your own matches")

        if not pair.proof_uploaded:
            raise HTTPException(status_code=400, detail="No proof uploaded yet")

        if pair.proof_confirmed:
            raise HTTPException(status_code=400, detail="Proof already confirmed")

        # Check if confirmation deadline has passed
        now = datetime.utcnow()
        if pair.confirmation_deadline and now > pair.confirmation_deadline:
            raise HTTPException(
                status_code=400,
                detail="Confirmation deadline has passed (4 hours). Your account will be temporarily blocked. Contact admin to unblock."
            )

        # Confirm proof and update balances
        pair.proof_confirmed = True
        pair.proof_confirmed_at = now
        pair.completed_at = now

        # Get funding and withdrawal requests
        funding_req = db.query(FundingRequest).filter(FundingRequest.id == pair.funding_request_id).first()
        funder_wallet = db.query(Wallet).filter(Wallet.id == funding_req.wallet_id).first()
        withdrawer_wallet = wallet

        # Update funder wallet (add funds)
        funder_wallet.balance += pair.amount
        funder_wallet.total_deposited += pair.amount

        # Update withdrawer wallet (deduct funds)
        withdrawer_wallet.balance -= pair.amount

        # Create transaction records
        funder_tx = WalletLog(
            id=uuid.uuid4(),
            wallet_id=funder_wallet.id,
            transaction_type="DEPOSIT",
            amount=pair.amount,
            balance_after=funder_wallet.balance,
            description=f"P2P Funding from {withdrawer_wallet.user_id}",
            created_at=datetime.utcnow()
        )
        db.add(funder_tx)

        withdrawer_tx = WalletLog(
            id=uuid.uuid4(),
            wallet_id=withdrawer_wallet.id,
            transaction_type="WITHDRAWAL",
            amount=pair.amount,
            balance_after=withdrawer_wallet.balance,
            description=f"P2P Withdrawal to {funder_wallet.user_id}",
            created_at=datetime.utcnow()
        )
        db.add(withdrawer_tx)

        # Check if requests are fully completed
        funding_pairs = db.query(FundingMatchPair).filter(
            FundingMatchPair.funding_request_id == funding_req.id
        ).all()
        if all(p.proof_confirmed for p in funding_pairs):
            funding_req.is_completed = True

        withdrawal_pairs = db.query(FundingMatchPair).filter(
            FundingMatchPair.withdrawal_request_id == withdrawal_req.id
        ).all()
        if all(p.proof_confirmed for p in withdrawal_pairs):
            withdrawal_req.is_completed = True

        # Schedule proof image deletion for 7 days from now
        if pair.proof_url:
            try:
                from azure_blob_service import azure_blob_service
                azure_blob_service.schedule_deletion(pair.proof_url, days=7)
                logger.info(f"Scheduled deletion for proof: {pair.proof_url}")
            except Exception as e:
                logger.warning(f"Could not schedule blob deletion: {e}")

        db.commit()

        return SuccessResponse(
            message="Payment confirmed! Balances updated.",
            data={
                "pair_id": str(pair.id),
                "amount": str(pair.amount),
                "funder_new_balance": str(funder_wallet.balance),
                "withdrawer_new_balance": str(withdrawer_wallet.balance)
            }
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.post("/match-pair/{pair_id}/request-extension", tags=["Proof"])
async def request_extension(
    pair_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Request a 1-hour extension for proof upload deadline (funder only).
    Can only be requested once and only before proof is uploaded.
    """
    try:
        pair = db.query(FundingMatchPair).filter(FundingMatchPair.id == uuid.UUID(pair_id)).first()
        if not pair:
            raise HTTPException(status_code=404, detail="Match pair not found")

        # Verify user is the funder
        funding_req = db.query(FundingRequest).filter(FundingRequest.id == pair.funding_request_id).first()
        if not funding_req:
            raise HTTPException(status_code=404, detail="Funding request not found")

        wallet = db.query(Wallet).filter(Wallet.id == funding_req.wallet_id).first()
        if str(wallet.user_id) != user_id:
            raise HTTPException(status_code=403, detail="You can only request extension for your own matches")

        # Check if already requested
        if pair.extension_requested:
            raise HTTPException(status_code=400, detail="Extension already requested")

        # Check if proof already uploaded
        if pair.proof_uploaded:
            raise HTTPException(status_code=400, detail="Cannot request extension after uploading proof")

        # Check if original deadline has passed
        now = datetime.utcnow()
        if pair.proof_deadline and now > pair.proof_deadline:
            raise HTTPException(
                status_code=400,
                detail="Original deadline has already passed. Cannot request extension."
            )

        # Grant extension
        pair.extension_requested = True
        pair.extension_granted = True
        pair.extended_deadline = pair.proof_deadline + timedelta(hours=1)
        db.commit()

        return SuccessResponse(
            message="Extension granted! You now have an additional 1 hour to upload proof.",
            data={
                "pair_id": str(pair.id),
                "original_deadline": pair.proof_deadline.isoformat(),
                "new_deadline": pair.extended_deadline.isoformat(),
                "extension_hours": 1
            }
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e)})


# ========================================
# ADMIN ENDPOINTS
# ========================================

@app.get("/admin/dashboard", tags=["Admin"])
async def get_admin_dashboard(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get admin dashboard overview - requires admin user"""
    try:
        # Check if user is admin
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Get next merge cycle
        next_cycle = get_next_merge_cycle(db)

        # Get admin wallets
        admin_wallets = db.query(AdminWallet).all()

        # Get unmatched requests count
        unmatched_funding = db.query(FundingRequest).filter(
            FundingRequest.is_fully_matched == False,
            FundingRequest.is_completed == False
        ).count()

        unmatched_withdrawal = db.query(WithdrawalRequest).filter(
            WithdrawalRequest.is_fully_matched == False,
            WithdrawalRequest.is_completed == False
        ).count()

        # Get recent merge cycles
        recent_cycles = db.query(MergeCycle).order_by(
            desc(MergeCycle.scheduled_time)
        ).limit(10).all()

        return SuccessResponse(
            message="Admin dashboard data",
            data={
                "next_merge_cycle": {
                    "id": str(next_cycle.id) if next_cycle else None,
                    "scheduled_time": next_cycle.scheduled_time.isoformat() if next_cycle else None,
                    "cutoff_time": next_cycle.cutoff_time.isoformat() if next_cycle else None,
                    "status": next_cycle.status if next_cycle else None
                } if next_cycle else None,
                "admin_wallets": [{
                    "id": str(w.id),
                    "wallet_type": w.wallet_type,
                    "currency": w.currency,
                    "balance": str(w.balance),
                    "total_funded": str(w.total_funded),
                    "total_received": str(w.total_received)
                } for w in admin_wallets],
                "unmatched_counts": {
                    "funding": unmatched_funding,
                    "withdrawal": unmatched_withdrawal
                },
                "recent_cycles": [{
                    "id": str(c.id),
                    "scheduled_time": c.scheduled_time.isoformat(),
                    "status": c.status,
                    "matched_pairs": c.matched_pairs,
                    "unmatched_funding": c.unmatched_funding,
                    "unmatched_withdrawal": c.unmatched_withdrawal
                } for c in recent_cycles]
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.get("/admin/unmatched-requests", tags=["Admin"])
async def get_unmatched_requests(
    currency: str = Query(..., description="NAIRA or USDT"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get all unmatched funding and withdrawal requests"""
    try:
        # Check if user is admin
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Get unmatched funding requests
        funding_requests = db.query(FundingRequest).join(Wallet).filter(
            Wallet.currency == currency.upper(),
            FundingRequest.is_fully_matched == False,
            FundingRequest.is_completed == False
        ).all()

        # Get unmatched withdrawal requests
        withdrawal_requests = db.query(WithdrawalRequest).join(Wallet).filter(
            Wallet.currency == currency.upper(),
            WithdrawalRequest.is_fully_matched == False,
            WithdrawalRequest.is_completed == False
        ).all()

        funding_data = []
        for req in funding_requests:
            wallet = db.query(Wallet).filter(Wallet.id == req.wallet_id).first()
            user_obj = db.query(User).filter(User.id == wallet.user_id).first() if wallet else None
            funding_data.append({
                "id": str(req.id),
                "amount": str(req.amount),
                "amount_remaining": str(req.amount_remaining),
                "user": {
                    "username": user_obj.username if user_obj else "Unknown",
                    "phone": user_obj.phone if user_obj else "Unknown"
                },
                "requested_at": req.requested_at.isoformat()
            })

        withdrawal_data = []
        for req in withdrawal_requests:
            wallet = db.query(Wallet).filter(Wallet.id == req.wallet_id).first()
            user_obj = db.query(User).filter(User.id == wallet.user_id).first() if wallet else None
            withdrawal_data.append({
                "id": str(req.id),
                "amount": str(req.amount),
                "amount_remaining": str(req.amount_remaining),
                "user": {
                    "username": user_obj.username if user_obj else "Unknown",
                    "phone": user_obj.phone if user_obj else "Unknown"
                },
                "requested_at": req.requested_at.isoformat()
            })

        return SuccessResponse(
            message="Unmatched requests retrieved",
            data={
                "funding": funding_data,
                "withdrawal": withdrawal_data,
                "currency": currency.upper()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.post("/admin/manual-match", tags=["Admin"])
async def manual_match_requests(
    funding_request_id: str = Query(...),
    withdrawal_request_id: str = Query(...),
    amount: Decimal = Query(...),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Manually match a funding request with a withdrawal request"""
    try:
        # Check if user is admin
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Get requests
        funding_req = db.query(FundingRequest).filter(
            FundingRequest.id == uuid.UUID(funding_request_id)
        ).first()
        withdrawal_req = db.query(WithdrawalRequest).filter(
            WithdrawalRequest.id == uuid.UUID(withdrawal_request_id)
        ).first()

        if not funding_req or not withdrawal_req:
            raise HTTPException(status_code=404, detail="Request not found")

        # Validate amount
        if amount > funding_req.amount_remaining or amount > withdrawal_req.amount_remaining:
            raise HTTPException(status_code=400, detail="Amount exceeds remaining balance")

        # Get or create merge cycle
        next_cycle = get_next_merge_cycle(db)
        if not next_cycle:
            raise HTTPException(status_code=400, detail="No merge cycle available")

        # Create match pair
        pair = FundingMatchPair(
            id=uuid.uuid4(),
            funding_request_id=funding_req.id,
            withdrawal_request_id=withdrawal_req.id,
            merge_cycle_id=next_cycle.id,
            amount=amount,
            proof_uploaded=False,
            proof_confirmed=False,
            created_at=datetime.utcnow()
        )
        db.add(pair)

        # Update amounts
        funding_req.amount_remaining -= amount
        withdrawal_req.amount_remaining -= amount

        # Check if fully matched
        if funding_req.amount_remaining == 0:
            funding_req.is_fully_matched = True
            funding_req.matched_at = datetime.utcnow()
            funding_req.merge_cycle_id = next_cycle.id

        if withdrawal_req.amount_remaining == 0:
            withdrawal_req.is_fully_matched = True
            withdrawal_req.matched_at = datetime.utcnow()
            withdrawal_req.merge_cycle_id = next_cycle.id

        db.commit()

        return SuccessResponse(
            message="Manual match created successfully",
            data={
                "pair_id": str(pair.id),
                "amount": str(amount),
                "funding_remaining": str(funding_req.amount_remaining),
                "withdrawal_remaining": str(withdrawal_req.amount_remaining)
            }
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.post("/admin/match-with-admin-wallet", tags=["Admin"])
async def match_with_admin_wallet(
    request_id: str = Query(...),
    request_type: str = Query(..., description="funding or withdrawal"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Match a user request with admin wallet"""
    try:
        # Check if user is admin
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        if request_type == "funding":
            # User wants to fund, admin acts as withdrawer
            funding_req = db.query(FundingRequest).filter(
                FundingRequest.id == uuid.UUID(request_id)
            ).first()

            if not funding_req:
                raise HTTPException(status_code=404, detail="Funding request not found")

            wallet = db.query(Wallet).filter(Wallet.id == funding_req.wallet_id).first()
            if not wallet:
                raise HTTPException(status_code=404, detail="Wallet not found")

            # Get admin wallet
            admin_wallet = db.query(AdminWallet).filter(
                AdminWallet.wallet_type == "funding_pool",
                AdminWallet.currency == wallet.currency
            ).first()

            if not admin_wallet:
                raise HTTPException(status_code=404, detail="Admin wallet not found")

            # Admin receives the money
            amount = funding_req.amount_remaining
            admin_wallet.balance += amount
            admin_wallet.total_received += amount

            funding_req.amount_remaining = Decimal("0")
            funding_req.is_fully_matched = True
            funding_req.is_completed = True
            funding_req.matched_at = datetime.utcnow()

            # Credit user wallet immediately (admin match)
            wallet.balance += amount
            wallet.total_deposited += amount

            # Create transaction
            tx = WalletLog(
                id=uuid.uuid4(),
                wallet_id=wallet.id,
                transaction_type="DEPOSIT",
                amount=amount,
                balance_after=wallet.balance,
                description="P2P Funding (Admin Match)",
                created_at=datetime.utcnow()
            )
            db.add(tx)

            db.commit()

            return SuccessResponse(
                message="Matched with admin wallet successfully",
                data={
                    "request_id": str(funding_req.id),
                    "amount": str(amount),
                    "admin_wallet_new_balance": str(admin_wallet.balance),
                    "user_wallet_new_balance": str(wallet.balance)
                }
            )

        else:  # withdrawal
            # User wants to withdraw, admin acts as funder
            withdrawal_req = db.query(WithdrawalRequest).filter(
                WithdrawalRequest.id == uuid.UUID(request_id)
            ).first()

            if not withdrawal_req:
                raise HTTPException(status_code=404, detail="Withdrawal request not found")

            wallet = db.query(Wallet).filter(Wallet.id == withdrawal_req.wallet_id).first()
            if not wallet:
                raise HTTPException(status_code=404, detail="Wallet not found")

            # Get admin wallet
            admin_wallet = db.query(AdminWallet).filter(
                AdminWallet.wallet_type == "funding_pool",
                AdminWallet.currency == wallet.currency
            ).first()

            if not admin_wallet:
                raise HTTPException(status_code=404, detail="Admin wallet not found")

            amount = withdrawal_req.amount_remaining

            # Check admin wallet has enough
            if admin_wallet.balance < amount:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient admin wallet balance. Available: {admin_wallet.balance}, Required: {amount}"
                )

            # Admin sends money
            admin_wallet.balance -= amount
            admin_wallet.total_funded += amount

            withdrawal_req.amount_remaining = Decimal("0")
            withdrawal_req.is_fully_matched = True
            withdrawal_req.is_completed = True
            withdrawal_req.matched_at = datetime.utcnow()

            # Deduct from user wallet
            wallet.balance -= amount

            # Create transaction
            tx = WalletLog(
                id=uuid.uuid4(),
                wallet_id=wallet.id,
                transaction_type="WITHDRAWAL",
                amount=amount,
                balance_after=wallet.balance,
                description="P2P Withdrawal (Admin Match)",
                created_at=datetime.utcnow()
            )
            db.add(tx)

            db.commit()

            return SuccessResponse(
                message="Matched with admin wallet successfully",
                data={
                    "request_id": str(withdrawal_req.id),
                    "amount": str(amount),
                    "admin_wallet_new_balance": str(admin_wallet.balance),
                    "user_wallet_new_balance": str(wallet.balance)
                }
            )

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.post("/admin/trigger-merge-cycle", tags=["Admin"])
async def trigger_merge_cycle_manually(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Manually trigger the next merge cycle (for testing)"""
    try:
        # Check if user is admin
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        next_cycle = get_next_merge_cycle(db)
        if not next_cycle:
            raise HTTPException(status_code=404, detail="No pending merge cycle found")

        # Trigger Celery task
        from funding_service.celery_batch_matching import run_merge_cycle
        task = run_merge_cycle.delay(str(next_cycle.id))

        return SuccessResponse(
            message="Merge cycle triggered",
            data={
                "cycle_id": str(next_cycle.id),
                "task_id": task.id,
                "scheduled_time": next_cycle.scheduled_time.isoformat()
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.post("/admin/unblock-user", tags=["Admin"])
async def unblock_user(
    user_email: str = Query(..., description="Email of user to unblock"),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Unblock a user who was temporarily blocked for missing deadlines"""
    try:
        # Check if user is admin
        admin_user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not admin_user or not admin_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Find user to unblock
        target_user = db.query(User).filter(User.email == user_email.lower()).first()
        if not target_user:
            raise HTTPException(status_code=404, detail=f"User with email {user_email} not found")

        # Get all wallets for this user
        wallets = db.query(Wallet).filter(Wallet.user_id == target_user.id).all()

        if not wallets:
            raise HTTPException(status_code=404, detail="No wallets found for this user")

        # Unblock all wallets
        unblocked_count = 0
        for wallet in wallets:
            if wallet.is_blocked:
                wallet.is_blocked = False
                unblocked_count += 1

        db.commit()

        if unblocked_count == 0:
            return SuccessResponse(
                message=f"User {target_user.username} was not blocked",
                data={
                    "user_id": str(target_user.id),
                    "username": target_user.username,
                    "email": target_user.email,
                    "was_blocked": False
                }
            )

        return SuccessResponse(
            message=f"Successfully unblocked user {target_user.username}",
            data={
                "user_id": str(target_user.id),
                "username": target_user.username,
                "email": target_user.email,
                "wallets_unblocked": unblocked_count,
                "warning": "User has been given another chance. They will be blocked again if they miss future deadlines."
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.get("/admin/blocked-users", tags=["Admin"])
async def get_blocked_users(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get list of all blocked users"""
    try:
        # Check if user is admin
        admin_user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not admin_user or not admin_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Find all blocked wallets
        blocked_wallets = db.query(Wallet).filter(Wallet.is_blocked == True).all()

        # Get unique users
        user_ids = set(w.user_id for w in blocked_wallets)
        blocked_users = []

        for uid in user_ids:
            user = db.query(User).filter(User.id == uid).first()
            if user:
                user_wallets = [w for w in blocked_wallets if w.user_id == uid]
                blocked_users.append({
                    "user_id": str(user.id),
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "blocked_wallets": [w.currency.value for w in user_wallets]
                })

        return SuccessResponse(
            message=f"Found {len(blocked_users)} blocked users",
            data={"blocked_users": blocked_users, "total_count": len(blocked_users)}
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


# ========================================
# DEMO/TEST ENDPOINTS
# ========================================

@app.post("/demo/trigger-merge", tags=["Demo"], status_code=status.HTTP_200_OK)
async def demo_trigger_merge(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    DEMO ONLY: Manually trigger a merge cycle for testing purposes.
    This bypasses the scheduled merge times and runs matching immediately.

    **WARNING**: This is for testing only. Remove before production!
    """
    try:
        # Verify user is admin
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required for demo endpoints")

        # Import the matching logic
        from auto_matcher import run_matching

        # Run the batch matching
        logger.info(f"[DEMO] Manual merge triggered by admin user {user_id}")
        run_matching()
        result = {"status": "completed", "message": "Batch matching executed"}

        return SuccessResponse(
            message="Demo merge completed successfully",
            data={
                "triggered_by": user.username,
                "merge_result": result,
                "note": "This was a demo merge triggered manually"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"[DEMO] Error during manual merge: {str(e)}\n{error_trace}")
        raise HTTPException(status_code=500, detail={"error": str(e), "trace": error_trace})


@app.get("/demo/pending-requests", tags=["Demo"])
async def demo_get_pending_requests(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    DEMO ONLY: Get summary of all pending funding and withdrawal requests.
    Useful for seeing what will be matched in the next merge.
    """
    try:
        # Verify user is admin
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required for demo endpoints")

        # Get pending funding requests
        pending_funding = db.query(FundingRequest).filter(
            FundingRequest.is_fully_matched == False,
            FundingRequest.is_completed == False
        ).all()

        # Get pending withdrawal requests
        pending_withdrawals = db.query(WithdrawalRequest).filter(
            WithdrawalRequest.is_fully_matched == False,
            WithdrawalRequest.is_completed == False
        ).all()

        funding_summary = []
        for fr in pending_funding:
            wallet = db.query(Wallet).filter(Wallet.id == fr.wallet_id).first()
            user_obj = db.query(User).filter(User.id == wallet.user_id).first()
            funding_summary.append({
                "id": str(fr.id),
                "username": user_obj.username if user_obj else "Unknown",
                "currency": wallet.currency.value if wallet else "Unknown",
                "amount": float(fr.amount),
                "amount_remaining": float(fr.amount_remaining),
                "requested_at": fr.requested_at.isoformat(),
                "opted_in": fr.opted_in
            })

        withdrawal_summary = []
        for wr in pending_withdrawals:
            wallet = db.query(Wallet).filter(Wallet.id == wr.wallet_id).first()
            user_obj = db.query(User).filter(User.id == wallet.user_id).first()
            withdrawal_summary.append({
                "id": str(wr.id),
                "username": user_obj.username if user_obj else "Unknown",
                "currency": wallet.currency.value if wallet else "Unknown",
                "amount": float(wr.amount),
                "amount_remaining": float(wr.amount_remaining),
                "requested_at": wr.requested_at.isoformat(),
                "opted_in": wr.opted_in
            })

        return SuccessResponse(
            message="Pending requests summary",
            data={
                "funding_requests": {
                    "count": len(pending_funding),
                    "total_naira": sum(float(f.amount_remaining) for f in pending_funding if db.query(Wallet).filter(Wallet.id == f.wallet_id).first().currency.value == "NAIRA"),
                    "total_usdt": sum(float(f.amount_remaining) for f in pending_funding if db.query(Wallet).filter(Wallet.id == f.wallet_id).first().currency.value == "USDT"),
                    "requests": funding_summary
                },
                "withdrawal_requests": {
                    "count": len(pending_withdrawals),
                    "total_naira": sum(float(w.amount_remaining) for w in pending_withdrawals if db.query(Wallet).filter(Wallet.id == w.wallet_id).first().currency.value == "NAIRA"),
                    "total_usdt": sum(float(w.amount_remaining) for w in pending_withdrawals if db.query(Wallet).filter(Wallet.id == w.wallet_id).first().currency.value == "USDT"),
                    "requests": withdrawal_summary
                }
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
