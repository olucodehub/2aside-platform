"""
Wallet Service - 2-Aside Platform
Handles wallet management, balance queries, currency switching, and transaction history
"""

from fastapi import FastAPI, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
import sys
import os
import uuid
from typing import Optional
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared import (
    get_db,
    User,
    Wallet,
    BankDetails,
    Transaction,
    WalletResponse,
    BalanceResponse,
    TransactionResponse,
    SwitchCurrencyRequest,
    SuccessResponse,
    PaginatedResponse,
    PaginationMeta,
    get_current_user_id,
    WalletNotFoundError,
    InvalidCurrencyError,
    TwoAsideBaseException,
    CurrencyType,
    calculate_pagination,
    get_offset_limit,
    format_currency,
)

# Import referral reward logic
from referral_rewards import check_and_pay_referral_reward_on_win

# Initialize FastAPI app
app = FastAPI(
    title="2-Aside Wallet Service",
    description="Wallet management and transaction service for 2-Aside Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# HEALTH CHECK
# ========================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "wallet-service"}


# ========================================
# GET ALL WALLETS
# ========================================

@app.get(
    "/wallets",
    response_model=SuccessResponse,
    tags=["Wallet"]
)
async def get_all_wallets(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get all wallets for current user (Naira + USDT).

    Returns both wallet instances with complete details.
    """
    try:
        # Get all wallets for user
        wallets = db.query(Wallet).filter(Wallet.user_id == uuid.UUID(user_id)).all()

        if not wallets:
            raise WalletNotFoundError()

        wallet_data = []
        for wallet in wallets:
            wallet_data.append({
                "id": str(wallet.id),
                "user_id": str(wallet.user_id),
                "currency": wallet.currency.value,
                "balance": str(wallet.balance),
                "total_deposited": str(wallet.total_deposited),
                "total_won": str(wallet.total_won),
                "total_withdrawn": str(wallet.total_withdrawn),
                "is_blocked": wallet.is_blocked,
                "referral_code": wallet.referral_code,
                "has_won_before": wallet.has_won_before,
                "wallet_address": wallet.wallet_address,
                "bank_details_id": str(wallet.bank_details_id) if wallet.bank_details_id else None,
                "created_at": wallet.created_at.isoformat() if wallet.created_at else None
            })

        return SuccessResponse(
            message="Wallets retrieved successfully",
            data={"wallets": wallet_data}
        )

    except TwoAsideBaseException as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# GET WALLET BY CURRENCY
# ========================================

@app.get(
    "/wallets/{currency}",
    response_model=SuccessResponse,
    tags=["Wallet"]
)
async def get_wallet_by_currency(
    currency: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get wallet for specific currency (NAIRA or USDT).
    """
    try:
        # Validate currency
        currency_upper = currency.upper()
        if currency_upper not in ["NAIRA", "USDT"]:
            raise InvalidCurrencyError(currency=currency)

        # Get wallet
        wallet = db.query(Wallet).filter(
            Wallet.user_id == uuid.UUID(user_id),
            Wallet.currency == currency_upper
        ).first()

        if not wallet:
            raise WalletNotFoundError()

        # Build wallet response
        wallet_data = {
            "id": str(wallet.id),
            "user_id": str(wallet.user_id),
            "currency": wallet.currency.value,
            "balance": str(wallet.balance),
            "balance_formatted": format_currency(wallet.balance, wallet.currency.value),
            "total_deposited": str(wallet.total_deposited),
            "total_won": str(wallet.total_won),
            "total_withdrawn": str(wallet.total_withdrawn),
            "is_blocked": wallet.is_blocked,
            "referral_code": wallet.referral_code,
            "has_won_before": wallet.has_won_before,
            "consecutive_cancellations": wallet.consecutive_cancellations or 0,
            "consecutive_misses": wallet.consecutive_misses or 0,
            "wallet_address": wallet.wallet_address,
            "bank_details_id": str(wallet.bank_details_id) if wallet.bank_details_id else None,
            "created_at": wallet.created_at.isoformat() if wallet.created_at else None
        }

        # Include bank details if they exist
        if wallet.bank_details:
            wallet_data["bank_details"] = {
                "account_number": wallet.bank_details.account_number,
                "account_name": wallet.bank_details.account_name,
                "bank_name": wallet.bank_details.bank_name,
                "bank_code": wallet.bank_details.bank_code
            }

        return SuccessResponse(
            message=f"{currency_upper} wallet retrieved successfully",
            data={"wallet": wallet_data}
        )

    except TwoAsideBaseException as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# GET BALANCE
# ========================================

@app.get(
    "/balance/{currency}",
    response_model=BalanceResponse,
    tags=["Wallet"]
)
async def get_balance(
    currency: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current balance for specific currency.

    Quick endpoint for checking balance only.
    """
    try:
        # Validate currency
        currency_upper = currency.upper()
        if currency_upper not in ["NAIRA", "USDT"]:
            raise InvalidCurrencyError(currency=currency)

        # Get wallet
        wallet = db.query(Wallet).filter(
            Wallet.user_id == uuid.UUID(user_id),
            Wallet.currency == currency_upper
        ).first()

        if not wallet:
            raise WalletNotFoundError()

        return BalanceResponse(
            wallet_id=str(wallet.id),
            currency=wallet.currency.value,
            balance=wallet.balance
        )

    except TwoAsideBaseException as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# SWITCH CURRENCY
# ========================================

@app.post(
    "/switch-currency",
    response_model=SuccessResponse,
    tags=["Wallet"]
)
async def switch_currency(
    request: SwitchCurrencyRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Switch active currency dashboard (Naira <-> USDT).

    This endpoint returns the wallet details for the requested currency.
    The frontend should use this to switch between currency views.
    """
    try:
        # Get wallet for requested currency
        wallet = db.query(Wallet).filter(
            Wallet.user_id == uuid.UUID(user_id),
            Wallet.currency == request.currency
        ).first()

        if not wallet:
            raise WalletNotFoundError()

        return SuccessResponse(
            message=f"Switched to {request.currency} dashboard",
            data={
                "active_wallet": {
                    "id": str(wallet.id),
                    "currency": wallet.currency.value,
                    "balance": str(wallet.balance),
                    "balance_formatted": format_currency(wallet.balance, wallet.currency.value),
                    "is_blocked": wallet.is_blocked,
                    "referral_code": wallet.referral_code
                }
            }
        )

    except TwoAsideBaseException as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# GET TRANSACTION HISTORY
# ========================================

@app.get(
    "/transactions/{currency}",
    response_model=PaginatedResponse,
    tags=["Transactions"]
)
async def get_transaction_history(
    currency: str,
    user_id: str = Depends(get_current_user_id),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get transaction history for specific currency with pagination.

    Returns paginated list of all transactions (deposits, withdrawals, bets, wins, etc.)
    """
    try:
        # Validate currency
        currency_upper = currency.upper()
        if currency_upper not in ["NAIRA", "USDT"]:
            raise InvalidCurrencyError(currency=currency)

        # Get wallet
        wallet = db.query(Wallet).filter(
            Wallet.user_id == uuid.UUID(user_id),
            Wallet.currency == currency_upper
        ).first()

        if not wallet:
            raise WalletNotFoundError()

        # Count total transactions
        total_items = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id
        ).count()

        # Calculate pagination
        pagination = calculate_pagination(page, per_page, total_items)
        offset, limit = get_offset_limit(page, per_page)

        # Get transactions
        transactions = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id
        ).order_by(desc(Transaction.created_at)).offset(offset).limit(limit).all()

        # Format transactions
        transaction_data = []
        for txn in transactions:
            transaction_data.append({
                "id": str(txn.id),
                "wallet_id": str(txn.wallet_id),
                "transaction_type": txn.transaction_type.value,
                "amount": str(txn.amount),
                "amount_formatted": format_currency(txn.amount, currency_upper),
                "balance_before": str(txn.balance_before),
                "balance_after": str(txn.balance_after),
                "description": txn.description,
                "reference": txn.reference,
                "created_at": txn.created_at.isoformat() if txn.created_at else None
            })

        return PaginatedResponse(
            success=True,
            data=transaction_data,
            meta=PaginationMeta(**pagination)
        )

    except TwoAsideBaseException as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# GET WALLET STATISTICS
# ========================================

@app.get(
    "/stats/{currency}",
    response_model=SuccessResponse,
    tags=["Wallet"]
)
async def get_wallet_stats(
    currency: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get wallet statistics and summary for specific currency.

    Returns:
        - Total deposited
        - Total won
        - Total withdrawn
        - Net profit/loss
        - Transaction counts
    """
    try:
        # Validate currency
        currency_upper = currency.upper()
        if currency_upper not in ["NAIRA", "USDT"]:
            raise InvalidCurrencyError(currency=currency)

        # Get wallet
        wallet = db.query(Wallet).filter(
            Wallet.user_id == uuid.UUID(user_id),
            Wallet.currency == currency_upper
        ).first()

        if not wallet:
            raise WalletNotFoundError()

        # Calculate net profit/loss
        net_profit = wallet.total_won - wallet.total_deposited

        # Count transactions by type
        from shared.constants import TransactionType
        deposit_count = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id,
            Transaction.transaction_type == TransactionType.DEPOSIT
        ).count()

        withdrawal_count = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id,
            Transaction.transaction_type == TransactionType.WITHDRAWAL
        ).count()

        win_count = db.query(Transaction).filter(
            Transaction.wallet_id == wallet.id,
            Transaction.transaction_type == TransactionType.WIN
        ).count()

        return SuccessResponse(
            message=f"{currency_upper} wallet statistics retrieved successfully",
            data={
                "statistics": {
                    "currency": currency_upper,
                    "current_balance": str(wallet.balance),
                    "total_deposited": str(wallet.total_deposited),
                    "total_won": str(wallet.total_won),
                    "total_withdrawn": str(wallet.total_withdrawn),
                    "net_profit": str(net_profit),
                    "transaction_counts": {
                        "deposits": deposit_count,
                        "withdrawals": withdrawal_count,
                        "wins": win_count
                    }
                }
            }
        )

    except TwoAsideBaseException as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# BANK ACCOUNT & WALLET ADDRESS
# ========================================

class SetBankAccountRequest(BaseModel):
    account_number: str
    account_name: str
    bank_name: str

class SetWalletAddressRequest(BaseModel):
    wallet_address: str  # BEP20 USDT address


@app.post(
    "/wallet/naira/bank-account",
    response_model=SuccessResponse,
    tags=["Wallet"]
)
async def set_naira_bank_account(
    request: SetBankAccountRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Set bank account for NAIRA wallet (One-time only, cannot be edited).
    Account name must match the user's registered name.
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get or create NAIRA wallet
        wallet = db.query(Wallet).filter(
            Wallet.user_id == uuid.UUID(user_id),
            Wallet.currency == CurrencyType.NAIRA
        ).first()

        if not wallet:
            # Create NAIRA wallet when user sets up bank details
            wallet = Wallet(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id),
                currency=CurrencyType.NAIRA,
                balance=0,
                total_deposited=0,
                total_won=0,
                consecutive_cancellations=0,
                consecutive_misses=0,
                is_blocked=False,
                has_won_before=False,
                referral_reward_paid=False,
                referral_code=generate_referral_code()
            )
            db.add(wallet)
            db.flush()

        # Check if bank account already set (non-editable)
        if wallet.bank_details_id:
            raise HTTPException(
                status_code=400,
                detail="Bank account already set and cannot be changed. Contact support if you made an error."
            )

        # Validate account name matches user's first and last name
        account_name_lower = request.account_name.lower().strip()
        first_name_lower = user.first_name.lower().strip()
        last_name_lower = user.last_name.lower().strip()

        # Check if both first name and last name appear in account name
        if first_name_lower not in account_name_lower or last_name_lower not in account_name_lower:
            raise HTTPException(
                status_code=400,
                detail=f"Account name must contain your registered first name ({user.first_name}) and last name ({user.last_name}). Please ensure the bank account is in your name."
            )

        # Create bank details
        bank_details = BankDetails(
            id=uuid.uuid4(),
            account_number=request.account_number.strip(),
            account_name=request.account_name.strip(),
            bank_name=request.bank_name.strip(),
            bank_code=None
        )

        db.add(bank_details)
        db.flush()

        # Update wallet with bank details
        wallet.bank_details_id = bank_details.id
        db.commit()
        db.refresh(wallet)

        return SuccessResponse(
            message="Bank account set successfully. Note: This cannot be changed later.",
            data={
                "account_number": bank_details.account_number,
                "account_name": bank_details.account_name,
                "bank_name": bank_details.bank_name,
                "warning": "Bank account details are permanent and cannot be edited. Contact support if you made an error."
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


@app.post(
    "/wallet/usdt/address",
    response_model=SuccessResponse,
    tags=["Wallet"]
)
async def set_usdt_wallet_address(
    request: SetWalletAddressRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Set BEP20 USDT wallet address (One-time only, cannot be edited).
    """
    try:
        # Get or create USDT wallet
        wallet = db.query(Wallet).filter(
            Wallet.user_id == uuid.UUID(user_id),
            Wallet.currency == CurrencyType.USDT
        ).first()

        if not wallet:
            # Create USDT wallet when user sets up wallet address
            wallet = Wallet(
                id=uuid.uuid4(),
                user_id=uuid.UUID(user_id),
                currency=CurrencyType.USDT,
                balance=0,
                total_deposited=0,
                total_won=0,
                consecutive_cancellations=0,
                consecutive_misses=0,
                is_blocked=False,
                has_won_before=False,
                referral_reward_paid=False,
                referral_code=generate_referral_code()
            )
            db.add(wallet)
            db.flush()

        # Check if wallet address already set (non-editable)
        if wallet.wallet_address:
            raise HTTPException(
                status_code=400,
                detail="USDT wallet address already set and cannot be changed. Contact support if you made an error."
            )

        # Basic validation: BEP20 addresses start with "0x" and are 42 characters
        address = request.wallet_address.strip()
        if not address.startswith("0x") or len(address) != 42:
            raise HTTPException(
                status_code=400,
                detail="Invalid BEP20 wallet address. Address must start with '0x' and be 42 characters long."
            )

        # Update wallet with address
        wallet.wallet_address = address
        db.commit()
        db.refresh(wallet)

        return SuccessResponse(
            message="USDT wallet address set successfully. Note: This cannot be changed later.",
            data={
                "wallet_address": wallet.wallet_address,
                "network": "BEP20 (Binance Smart Chain)",
                "warning": "Wallet address is permanent and cannot be edited. Contact support if you made an error."
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


@app.get(
    "/wallet/naira/bank-account",
    response_model=SuccessResponse,
    tags=["Wallet"]
)
async def get_naira_bank_account(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get NAIRA wallet bank account details"""
    try:
        wallet = db.query(Wallet).filter(
            Wallet.user_id == uuid.UUID(user_id),
            Wallet.currency == CurrencyType.NAIRA
        ).first()

        if not wallet:
            raise WalletNotFoundError()

        if not wallet.bank_details_id:
            return SuccessResponse(
                message="No bank account set",
                data={"has_bank_account": False}
            )

        bank_details = db.query(BankDetails).filter(BankDetails.id == wallet.bank_details_id).first()

        return SuccessResponse(
            message="Bank account retrieved",
            data={
                "has_bank_account": True,
                "account_number": bank_details.account_number,
                "account_name": bank_details.account_name,
                "bank_name": bank_details.bank_name
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


@app.get(
    "/wallet/usdt/address",
    response_model=SuccessResponse,
    tags=["Wallet"]
)
async def get_usdt_wallet_address(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get USDT wallet address"""
    try:
        wallet = db.query(Wallet).filter(
            Wallet.user_id == uuid.UUID(user_id),
            Wallet.currency == CurrencyType.USDT
        ).first()

        if not wallet:
            raise WalletNotFoundError()

        if not wallet.wallet_address:
            return SuccessResponse(
                message="No wallet address set",
                data={"has_wallet_address": False}
            )

        return SuccessResponse(
            message="Wallet address retrieved",
            data={
                "has_wallet_address": True,
                "wallet_address": wallet.wallet_address,
                "network": "BEP20 (Binance Smart Chain)"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# REFERRAL REWARDS
# ========================================

class ReferralRewardRequest(BaseModel):
    """Request to pay referral reward when a user wins"""
    winner_wallet_id: str
    platform_fee: float


@app.post(
    "/wallet/referral-reward",
    response_model=SuccessResponse,
    tags=["Wallet", "Referrals"]
)
async def pay_referral_reward_endpoint(
    request: ReferralRewardRequest,
    db: Session = Depends(get_db)
):
    """
    Pay referral reward to referrer when a referred user wins their first bet.
    This endpoint should be called by the betting service when a user wins.

    Args:
        winner_wallet_id: ID of the wallet that just won
        platform_fee: Platform fee collected from the win (5% goes to referrer)

    Returns:
        Success response indicating if reward was paid
    """
    try:
        platform_fee_decimal = Decimal(str(request.platform_fee))

        reward_paid = check_and_pay_referral_reward_on_win(
            db=db,
            winner_wallet_id=request.winner_wallet_id,
            platform_fee=platform_fee_decimal
        )

        if reward_paid:
            return SuccessResponse(
                message="Referral reward paid successfully",
                data={
                    "reward_paid": True,
                    "winner_wallet_id": request.winner_wallet_id,
                    "reward_amount": float(platform_fee_decimal * Decimal("0.05"))
                }
            )
        else:
            return SuccessResponse(
                message="No referral reward applicable",
                data={
                    "reward_paid": False,
                    "winner_wallet_id": request.winner_wallet_id,
                    "reason": "User has already won before, or was not referred, or reward already paid"
                }
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# RUN SERVER
# ========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
