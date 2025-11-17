"""
2-Aside Platform - Shared Pydantic Schemas
Common request/response validation models used across all microservices
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Any, Dict
from datetime import datetime
from decimal import Decimal
import re


# ========================================
# COMMON RESPONSE SCHEMAS
# ========================================

class SuccessResponse(BaseModel):
    """Standard success response wrapper"""
    success: bool = True
    message: str
    data: Optional[Any] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {"id": "123e4567-e89b-12d3-a456-426614174000"}
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response wrapper"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Validation failed",
                "detail": "Invalid email format",
                "error_code": "VALIDATION_ERROR"
            }
        }


class PaginationMeta(BaseModel):
    """Pagination metadata"""
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total_items: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = False
    has_prev: bool = False


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    success: bool = True
    data: List[Any]
    meta: PaginationMeta

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": [{"id": "123", "name": "Item 1"}],
                "meta": {
                    "page": 1,
                    "per_page": 20,
                    "total_items": 100,
                    "total_pages": 5,
                    "has_next": True,
                    "has_prev": False
                }
            }
        }


# ========================================
# AUTHENTICATION SCHEMAS
# ========================================

class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr = Field(..., description="Valid email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 chars)")
    first_name: str = Field(..., min_length=2, max_length=100, description="First name (2-100 chars)")
    last_name: str = Field(..., min_length=2, max_length=100, description="Last name (2-100 chars)")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    referral_code: Optional[str] = Field(None, max_length=20, description="Referral code (optional)")

    @validator('username')
    def validate_username(cls, v):
        """Username must be alphanumeric with underscores only"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.lower()

    @validator('password')
    def validate_password(cls, v):
        """Password must meet complexity requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        """Names must contain only letters and spaces"""
        if not re.match(r'^[a-zA-Z\s]+$', v):
            raise ValueError('Name can only contain letters and spaces')
        return v.strip().title()  # Remove extra spaces and capitalize properly

    @validator('phone')
    def validate_phone(cls, v):
        """Phone must be valid format"""
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
            raise ValueError('Invalid phone number format')
        return cleaned

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "john_doe",
                "phone": "+2348012345678",
                "password": "SecurePass123",
                "referral_code": "REF123"
            }
        }


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = 3600  # seconds
    user: Optional[Dict] = None  # Include user data for frontend

    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {"id": "123", "email": "user@example.com", "is_admin": False}
            }
        }


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="Refresh token")


# ========================================
# USER SCHEMAS
# ========================================

class UserResponse(BaseModel):
    """User profile response"""
    id: str
    email: str
    username: str
    phone: str
    is_admin: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "username": "john_doe",
                "phone": "+2348012345678",
                "is_admin": False,
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-20T14:20:00Z"
            }
        }


class UpdateUserRequest(BaseModel):
    """Update user profile request"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)

    @validator('username')
    def validate_username(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.lower() if v else v

    @validator('phone')
    def validate_phone(cls, v):
        if v is not None:
            cleaned = re.sub(r'[\s\-\(\)]', '', v)
            if not re.match(r'^\+?[0-9]{10,15}$', cleaned):
                raise ValueError('Invalid phone number format')
            return cleaned
        return v


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


# ========================================
# WALLET SCHEMAS
# ========================================

class CurrencyEnum(str):
    """Currency enumeration"""
    NAIRA = "NAIRA"
    USDT = "USDT"


class WalletResponse(BaseModel):
    """Wallet details response"""
    id: str
    user_id: str
    currency: str
    balance: Decimal
    total_deposited: Decimal
    total_won: Decimal
    total_withdrawn: Decimal
    is_blocked: bool = False
    referral_code: str
    has_won_before: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "wallet-123",
                "user_id": "user-456",
                "currency": "NAIRA",
                "balance": "15000.00",
                "total_deposited": "20000.00",
                "total_won": "5000.00",
                "total_withdrawn": "10000.00",
                "is_blocked": False,
                "referral_code": "REF123ABC",
                "has_won_before": True,
                "created_at": "2025-01-15T10:30:00Z"
            }
        }


class BalanceResponse(BaseModel):
    """Simple balance response"""
    wallet_id: str
    currency: str
    balance: Decimal

    class Config:
        json_schema_extra = {
            "example": {
                "wallet_id": "wallet-123",
                "currency": "NAIRA",
                "balance": "15000.00"
            }
        }


class SwitchCurrencyRequest(BaseModel):
    """Switch active currency request"""
    currency: str = Field(..., description="NAIRA or USDT")

    @validator('currency')
    def validate_currency(cls, v):
        if v.upper() not in ["NAIRA", "USDT"]:
            raise ValueError('Currency must be NAIRA or USDT')
        return v.upper()


# ========================================
# TRANSACTION SCHEMAS
# ========================================

class TransactionResponse(BaseModel):
    """Transaction record response"""
    id: str
    wallet_id: str
    transaction_type: str
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    description: Optional[str] = None
    reference: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "txn-123",
                "wallet_id": "wallet-456",
                "transaction_type": "win",
                "amount": "5000.00",
                "balance_before": "10000.00",
                "balance_after": "15000.00",
                "description": "Win from Game: Arsenal vs Chelsea",
                "reference": "game-789",
                "created_at": "2025-01-20T18:45:00Z"
            }
        }


# ========================================
# BETTING SCHEMAS
# ========================================

class BetSideEnum(str):
    """Bet side enumeration"""
    HOME = "home"
    AWAY = "away"


class BetTypeEnum(str):
    """Bet type enumeration"""
    RENDEZVOUS = "rendezvous"
    ONE_V_ONE = "1v1"
    CUSTOM = "custom"


class PlaceBetRequest(BaseModel):
    """Place bet request"""
    game_id: str = Field(..., description="Game UUID")
    amount: Decimal = Field(..., gt=0, description="Bet amount (must be positive)")
    side: str = Field(..., description="home or away")
    bet_type: str = Field(..., description="rendezvous, 1v1, or custom")
    currency: str = Field(..., description="NAIRA or USDT")

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Bet amount must be greater than 0')
        if v < 100:  # Minimum bet 100 Naira/USDT
            raise ValueError('Minimum bet amount is 100')
        if v > 1000000:  # Maximum bet 1M
            raise ValueError('Maximum bet amount is 1,000,000')
        return v

    @validator('side')
    def validate_side(cls, v):
        if v.lower() not in ["home", "away"]:
            raise ValueError('Side must be home or away')
        return v.lower()

    @validator('bet_type')
    def validate_bet_type(cls, v):
        if v.lower() not in ["rendezvous", "1v1", "custom"]:
            raise ValueError('Bet type must be rendezvous, 1v1, or custom')
        return v.lower()

    @validator('currency')
    def validate_currency(cls, v):
        if v.upper() not in ["NAIRA", "USDT"]:
            raise ValueError('Currency must be NAIRA or USDT')
        return v.upper()

    class Config:
        json_schema_extra = {
            "example": {
                "game_id": "game-123",
                "amount": "5000.00",
                "side": "home",
                "bet_type": "rendezvous",
                "currency": "NAIRA"
            }
        }


class BetResponse(BaseModel):
    """Bet registration response"""
    id: str
    wallet_id: str
    game_id: str
    amount: Decimal
    side: str
    bet_type: str
    status: str
    match_status: Optional[str] = None  # For 1v1: "waiting" or "matched"
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "bet-123",
                "wallet_id": "wallet-456",
                "game_id": "game-789",
                "amount": "5000.00",
                "side": "home",
                "bet_type": "1v1",
                "status": "active",
                "match_status": "matched",
                "created_at": "2025-01-20T16:30:00Z"
            }
        }


class GameResponse(BaseModel):
    """Game details response"""
    id: str
    title: str
    home_team: str
    away_team: str
    scheduled_time: datetime
    betting_closes_at: datetime
    status: str
    winner: Optional[str] = None

    # Pool totals (for Rendezvous bets)
    home_total_naira: Decimal = Decimal("0")
    away_total_naira: Decimal = Decimal("0")
    home_total_usdt: Decimal = Decimal("0")
    away_total_usdt: Decimal = Decimal("0")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "game-123",
                "title": "Premier League",
                "home_team": "Arsenal",
                "away_team": "Chelsea",
                "scheduled_time": "2025-01-25T15:00:00Z",
                "betting_closes_at": "2025-01-25T14:00:00Z",
                "status": "upcoming",
                "winner": None,
                "home_total_naira": "500000.00",
                "away_total_naira": "300000.00",
                "home_total_usdt": "1000.00",
                "away_total_usdt": "800.00"
            }
        }


# ========================================
# FUNDING SCHEMAS
# ========================================

class FundingRequestCreate(BaseModel):
    """Create funding request"""
    amount: Decimal = Field(..., gt=0, description="Amount to fund")
    currency: str = Field(..., description="NAIRA or USDT")

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v < 1000:  # Minimum funding 1000 Naira/USDT
            raise ValueError('Minimum funding amount is 1000')
        return v

    @validator('currency')
    def validate_currency(cls, v):
        if v.upper() not in ["NAIRA", "USDT"]:
            raise ValueError('Currency must be NAIRA or USDT')
        return v.upper()


class WithdrawalRequestCreate(BaseModel):
    """Create withdrawal request"""
    amount: Decimal = Field(..., gt=0, description="Amount to withdraw")
    currency: str = Field(..., description="NAIRA or USDT")

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v < 1000:  # Minimum withdrawal 1000
            raise ValueError('Minimum withdrawal amount is 1000')
        return v

    @validator('currency')
    def validate_currency(cls, v):
        if v.upper() not in ["NAIRA", "USDT"]:
            raise ValueError('Currency must be NAIRA or USDT')
        return v.upper()


class FundingMatchResponse(BaseModel):
    """Funding match details response"""
    id: str
    funder_wallet_id: str
    withdrawer_wallet_id: str
    amount: Decimal
    status: str
    proof_uploaded: bool = False
    proof_confirmed: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


# ========================================
# ADMIN SCHEMAS
# ========================================

class BlockUserRequest(BaseModel):
    """Block/unblock user request"""
    user_id: str = Field(..., description="User UUID")
    block: bool = Field(..., description="True to block, False to unblock")
    reason: Optional[str] = Field(None, description="Reason for blocking")


class SetGameResultRequest(BaseModel):
    """Set game result (admin only)"""
    game_id: str = Field(..., description="Game UUID")
    winner: str = Field(..., description="home, away, or draw")

    @validator('winner')
    def validate_winner(cls, v):
        if v.lower() not in ["home", "away", "draw"]:
            raise ValueError('Winner must be home, away, or draw')
        return v.lower()


class PlatformStatsResponse(BaseModel):
    """Platform statistics response"""
    total_users: int
    total_games: int
    total_bets: int
    total_volume_naira: Decimal
    total_volume_usdt: Decimal
    platform_revenue_naira: Decimal
    platform_revenue_usdt: Decimal
    active_users_today: int

    class Config:
        json_schema_extra = {
            "example": {
                "total_users": 15000,
                "total_games": 250,
                "total_bets": 50000,
                "total_volume_naira": "50000000.00",
                "total_volume_usdt": "100000.00",
                "platform_revenue_naira": "2500000.00",
                "platform_revenue_usdt": "5000.00",
                "active_users_today": 1200
            }
        }
