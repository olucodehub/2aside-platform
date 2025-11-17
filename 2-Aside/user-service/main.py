"""
User Service - 2-Aside Platform
Handles user profile management, password changes, and referral codes
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import sys
import os
import uuid
from typing import List

# Add parent directory to path for shared module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared import (
    get_db,
    User,
    Wallet,
    UserResponse,
    UpdateUserRequest,
    ChangePasswordRequest,
    SuccessResponse,
    ErrorResponse,
    get_current_user_id,
    get_current_user,
    hash_password,
    verify_password,
    UserNotFoundError,
    InvalidCredentialsError,
    TwoAsideBaseException,
    CurrencyType,
)

# Initialize FastAPI app
app = FastAPI(
    title="2-Aside User Service",
    description="User profile management service for 2-Aside Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
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
    return {"status": "healthy", "service": "user-service"}


# ========================================
# GET CURRENT USER PROFILE
# ========================================

@app.get(
    "/me",
    response_model=SuccessResponse,
    tags=["User Profile"]
)
async def get_current_user_profile(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get current user's profile information.

    Returns:
        - User details
        - Wallet information for both currencies
        - Referral codes
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # Get wallets
        wallets = db.query(Wallet).filter(Wallet.user_id == user.id).all()

        # Organize wallets by currency
        naira_wallet = next((w for w in wallets if w.currency == CurrencyType.NAIRA), None)
        usdt_wallet = next((w for w in wallets if w.currency == CurrencyType.USDT), None)

        return SuccessResponse(
            message="User profile retrieved successfully",
            data={
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "phone": user.phone,
                    "referral_code": user.referral_code,
                    "is_admin": user.is_admin,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                },
                "wallets": {
                    "naira": {
                        "id": str(naira_wallet.id) if naira_wallet else None,
                        "currency": "NAIRA",
                        "balance": str(naira_wallet.balance) if naira_wallet else "0.00",
                        "is_blocked": naira_wallet.is_blocked if naira_wallet else False
                    },
                    "usdt": {
                        "id": str(usdt_wallet.id) if usdt_wallet else None,
                        "currency": "USDT",
                        "balance": str(usdt_wallet.balance) if usdt_wallet else "0.00",
                        "is_blocked": usdt_wallet.is_blocked if usdt_wallet else False
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
# UPDATE USER PROFILE
# ========================================

@app.put(
    "/me",
    response_model=SuccessResponse,
    tags=["User Profile"]
)
async def update_user_profile(
    request: UpdateUserRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information.

    Can update:
        - Username
        - Phone number
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # Update fields if provided
        if request.username:
            # Check if username already taken
            existing = db.query(User).filter(
                User.username == request.username.lower(),
                User.id != user.id
            ).first()

            if existing:
                from shared.exceptions import DuplicateRegistrationError
                raise DuplicateRegistrationError(field="username")

            user.username = request.username.lower()

        if request.phone:
            user.phone = request.phone

        db.commit()
        db.refresh(user)

        return SuccessResponse(
            message="Profile updated successfully",
            data={
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "username": user.username,
                    "phone": user.phone,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                }
            }
        )

    except TwoAsideBaseException as e:
        db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# CHANGE PASSWORD
# ========================================

@app.put(
    "/password",
    response_model=SuccessResponse,
    tags=["User Profile"]
)
async def change_password(
    request: ChangePasswordRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Change user's password.

    Requires:
        - Current password (for verification)
        - New password (must meet complexity requirements)
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # Verify current password
        if not verify_password(request.current_password, user.password_hash):
            raise InvalidCredentialsError(message="Current password is incorrect")

        # Update password
        user.password_hash = hash_password(request.new_password)

        db.commit()

        return SuccessResponse(
            message="Password changed successfully",
            data=None
        )

    except TwoAsideBaseException as e:
        db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# GET REFERRAL CODES
# ========================================

@app.get(
    "/referral-codes",
    response_model=SuccessResponse,
    tags=["Referral"]
)
async def get_referral_codes(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get user's referral codes for both currencies.

    Returns separate referral codes for Naira and USDT wallets.
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # Get wallets
        wallets = db.query(Wallet).filter(Wallet.user_id == user.id).all()

        naira_wallet = next((w for w in wallets if w.currency == CurrencyType.NAIRA), None)
        usdt_wallet = next((w for w in wallets if w.currency == CurrencyType.USDT), None)

        return SuccessResponse(
            message="Referral codes retrieved successfully",
            data={
                "referral_codes": {
                    "naira": naira_wallet.referral_code if naira_wallet else None,
                    "usdt": usdt_wallet.referral_code if usdt_wallet else None
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
# GET REFERRAL STATS
# ========================================

@app.get(
    "/referral-stats",
    response_model=SuccessResponse,
    tags=["Referral"]
)
async def get_referral_stats(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Get user's referral statistics.

    Returns:
        - Total referrals (Naira)
        - Total referrals (USDT)
        - Total referral earnings (Naira)
        - Total referral earnings (USDT)
    """
    try:
        # Get user's wallets
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise UserNotFoundError(user_id=user_id)

        wallets = db.query(Wallet).filter(Wallet.user_id == user.id).all()

        naira_wallet = next((w for w in wallets if w.currency == CurrencyType.NAIRA), None)
        usdt_wallet = next((w for w in wallets if w.currency == CurrencyType.USDT), None)

        # Count referrals for each currency
        naira_referrals = 0
        usdt_referrals = 0

        if naira_wallet:
            naira_referrals = db.query(Wallet).filter(
                Wallet.referred_by_wallet_id == naira_wallet.id,
                Wallet.currency == CurrencyType.NAIRA
            ).count()

        if usdt_wallet:
            usdt_referrals = db.query(Wallet).filter(
                Wallet.referred_by_wallet_id == usdt_wallet.id,
                Wallet.currency == CurrencyType.USDT
            ).count()

        return SuccessResponse(
            message="Referral statistics retrieved successfully",
            data={
                "referral_stats": {
                    "naira": {
                        "total_referrals": naira_referrals,
                        "referral_code": naira_wallet.referral_code if naira_wallet else None
                    },
                    "usdt": {
                        "total_referrals": usdt_referrals,
                        "referral_code": usdt_wallet.referral_code if usdt_wallet else None
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
# RUN SERVER
# ========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )
