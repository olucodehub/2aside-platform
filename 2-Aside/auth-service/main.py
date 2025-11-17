"""
Auth Service - 2-Aside Platform
Handles user registration, login, and JWT token management
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import sys
import os
import uuid
from typing import Optional

# Add parent directory to path for shared module
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from shared import (
    get_db,
    User,
    Wallet,
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    SuccessResponse,
    ErrorResponse,
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_current_user_id,
    InvalidCredentialsError,
    DuplicateRegistrationError,
    UserNotFoundError,
    InvalidReferralCodeError,
    SelfReferralError,
    TwoAsideBaseException,
    generate_referral_code,
    validate_referral_code,
    CurrencyType,
)

# Initialize FastAPI app
app = FastAPI(
    title="2-Aside Auth Service",
    description="Authentication and registration service for 2-Aside Platform",
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
    return {"status": "healthy", "service": "auth-service"}


# ========================================
# REGISTRATION
# ========================================

@app.post(
    "/register",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"]
)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user with dual wallets (Naira + USDT).

    - Creates User account
    - Creates two Wallet instances (one for Naira, one for USDT)
    - Generates unique referral code for each wallet
    - Links referrer if referral code provided

    Returns:
        - User details
        - Access token
        - Refresh token
    """
    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise DuplicateRegistrationError(field="email")

        # Check if username already exists
        existing_username = db.query(User).filter(User.username == request.username).first()
        if existing_username:
            raise DuplicateRegistrationError(field="username")

        # Check if phone number already exists
        existing_phone = db.query(User).filter(User.phone == request.phone).first()
        if existing_phone:
            raise DuplicateRegistrationError(field="phone number")

        # Validate referral code if provided
        referrer_user = None

        if request.referral_code:
            if not validate_referral_code(request.referral_code):
                raise InvalidReferralCodeError(code=request.referral_code)

            # Find referrer by referral code in users table
            referrer_user = db.query(User).filter(
                User.referral_code == request.referral_code.upper()
            ).first()

            if not referrer_user:
                raise InvalidReferralCodeError(code=request.referral_code)

        # Generate unique referral code for new user
        new_referral_code = generate_referral_code()
        while db.query(User).filter(User.referral_code == new_referral_code).first():
            new_referral_code = generate_referral_code()

        # Create new user
        user_id = uuid.uuid4()
        new_user = User(
            id=user_id,
            email=request.email.lower(),
            username=request.username.lower(),
            first_name=request.first_name,
            last_name=request.last_name,
            phone=request.phone,
            password_hash=hash_password(request.password),
            referral_code=new_referral_code,
            referred_by_user_id=referrer_user.id if referrer_user else None,
            is_admin=False
        )

        db.add(new_user)
        db.commit()  # Commit user only, wallets will be created when payment details are added

        # Create JWT tokens
        access_token = create_access_token(data={"sub": str(user_id)})
        refresh_token = create_refresh_token(data={"sub": str(user_id)})

        return SuccessResponse(
            message="Registration successful. Please complete your payment setup.",
            data={
                "user": {
                    "id": str(user_id),
                    "email": new_user.email,
                    "username": new_user.username,
                    "phone": new_user.phone,
                    "referral_code": new_user.referral_code
                },
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer"
                }
            }
        )

    except TwoAsideBaseException as e:
        db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except IntegrityError as e:
        db.rollback()
        # Handle unique constraint violations
        if "email" in str(e):
            raise HTTPException(
                status_code=400,
                detail={"success": False, "error": "Email already registered"}
            )
        elif "username" in str(e):
            raise HTTPException(
                status_code=400,
                detail={"success": False, "error": "Username already taken"}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={"success": False, "error": "Registration failed"}
            )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# LOGIN
# ========================================

@app.post(
    "/login",
    response_model=TokenResponse,
    tags=["Authentication"]
)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.

    - Validates email and password
    - Returns access token (1 hour expiry)
    - Returns refresh token (30 days expiry)
    """
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email.lower()).first()

        if not user:
            raise InvalidCredentialsError()

        # Verify password
        if not verify_password(request.password, user.password_hash):
            raise InvalidCredentialsError()

        # Check if any wallet is blocked
        wallets = db.query(Wallet).filter(Wallet.user_id == user.id).all()
        blocked_wallets = [w for w in wallets if w.is_blocked]

        if blocked_wallets:
            from shared.exceptions import AccountBlockedError
            raise AccountBlockedError(
                message="Your account has been blocked. Please contact support.",
                reason="Excessive cancellations or missed payments"
            )

        # Create JWT tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        # Prepare user data for frontend
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "phone": user.phone,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=3600,  # 1 hour
            user=user_data
        )

    except TwoAsideBaseException as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# REFRESH TOKEN
# ========================================

@app.post(
    "/refresh",
    response_model=TokenResponse,
    tags=["Authentication"]
)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.

    - Validates refresh token
    - Issues new access token
    - Issues new refresh token
    """
    try:
        # Verify refresh token
        payload = verify_refresh_token(request.refresh_token)
        user_id = payload.get("sub")

        if not user_id:
            from shared.exceptions import InvalidTokenError
            raise InvalidTokenError()

        # Verify user still exists
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise UserNotFoundError(user_id=user_id)

        # Create new tokens
        access_token = create_access_token(data={"sub": str(user_id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user_id)})

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=3600
        )

    except TwoAsideBaseException as e:
        raise HTTPException(status_code=e.status_code, detail=e.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": "Internal server error", "detail": str(e)}
        )


# ========================================
# VERIFY TOKEN
# ========================================

@app.get(
    "/verify",
    response_model=SuccessResponse,
    tags=["Authentication"]
)
async def verify_token(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Verify JWT token and return user info.

    Used by other services to validate tokens.
    """
    try:
        # Get user
        user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
        if not user:
            raise UserNotFoundError(user_id=user_id)

        return SuccessResponse(
            message="Token is valid",
            data={
                "user_id": str(user.id),
                "email": user.email,
                "username": user.username,
                "is_admin": user.is_admin
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
        port=8001,
        reload=True,
        log_level="info"
    )
