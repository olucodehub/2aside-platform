"""
2-Aside Platform - Constants and Configuration
Platform-wide constants, limits, and configuration values
"""

from decimal import Decimal
from enum import Enum


# ========================================
# PLATFORM FEE STRUCTURE
# ========================================

# Platform commission (5% on all wins)
PLATFORM_FEE_PERCENTAGE = Decimal("0.05")  # 5%

# Referral bonus (paid FROM platform's 5% revenue on first win)
REFERRAL_BONUS_PERCENTAGE = Decimal("0.05")  # 5% (entire platform fee)

# Platform keeps 0% on first win with referrer
PLATFORM_FIRST_WIN_WITH_REFERRER = Decimal("0.00")  # 0%


# ========================================
# BETTING LIMITS
# ========================================

# Minimum bet amounts (in Naira/USDT)
MIN_BET_AMOUNT = Decimal("100.00")

# Maximum bet amounts (in Naira/USDT)
MAX_BET_AMOUNT = Decimal("1000000.00")  # 1 million

# Betting closes X hours before game start
BETTING_CLOSE_HOURS_BEFORE_GAME = 1

# Maximum bets per user per game
MAX_BETS_PER_GAME_PER_USER = 1  # One bet per game per currency


# ========================================
# FUNDING & WITHDRAWAL LIMITS
# ========================================

# Minimum funding amount
MIN_FUNDING_AMOUNT = Decimal("1000.00")

# Maximum funding amount per transaction
MAX_FUNDING_AMOUNT = Decimal("10000000.00")  # 10 million

# Minimum withdrawal amount
MIN_WITHDRAWAL_AMOUNT = Decimal("1000.00")

# Maximum withdrawal amount per transaction
MAX_WITHDRAWAL_AMOUNT = Decimal("10000000.00")  # 10 million

# Maximum daily withdrawal limit
MAX_DAILY_WITHDRAWAL_LIMIT = Decimal("50000000.00")  # 50 million

# Funding request expiration (hours)
FUNDING_REQUEST_EXPIRATION_HOURS = 24

# Withdrawal request expiration (hours)
WITHDRAWAL_REQUEST_EXPIRATION_HOURS = 24


# ========================================
# USER BEHAVIOR LIMITS
# ========================================

# Maximum consecutive cancellations before blocking
MAX_CONSECUTIVE_CANCELLATIONS = 3

# Maximum consecutive missed payments before blocking
MAX_CONSECUTIVE_MISSED_PAYMENTS = 3

# Days to wait before unblocking (if auto-unblock enabled)
AUTO_UNBLOCK_DAYS = 30


# ========================================
# AUTHENTICATION & SECURITY
# ========================================

# JWT token expiration (minutes)
JWT_ACCESS_TOKEN_EXPIRATION_MINUTES = 60  # 1 hour

# Refresh token expiration (days)
JWT_REFRESH_TOKEN_EXPIRATION_DAYS = 30  # 30 days

# Password minimum length
PASSWORD_MIN_LENGTH = 8

# Password complexity requirements
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_DIGIT = True
PASSWORD_REQUIRE_SPECIAL_CHAR = False

# Maximum login attempts before rate limiting
MAX_LOGIN_ATTEMPTS = 5
LOGIN_RATE_LIMIT_MINUTES = 15

# Session timeout (minutes of inactivity)
SESSION_TIMEOUT_MINUTES = 30


# ========================================
# REFERRAL SYSTEM
# ========================================

# Referral code length
REFERRAL_CODE_LENGTH = 8

# Referral code format (alphanumeric uppercase)
REFERRAL_CODE_PATTERN = r'^[A-Z0-9]{6,12}$'

# Referral bonus trigger (first win only)
REFERRAL_BONUS_TRIGGER = "first_win"


# ========================================
# PAGINATION
# ========================================

# Default items per page
DEFAULT_PAGE_SIZE = 20

# Maximum items per page
MAX_PAGE_SIZE = 100

# Minimum page number
MIN_PAGE_NUMBER = 1


# ========================================
# RATE LIMITING
# ========================================

# API rate limits (requests per minute)
RATE_LIMIT_GENERAL = 100  # General endpoints
RATE_LIMIT_AUTH = 10  # Login/register endpoints
RATE_LIMIT_BETTING = 30  # Betting endpoints
RATE_LIMIT_FUNDING = 20  # Funding/withdrawal endpoints

# Rate limit time window (seconds)
RATE_LIMIT_WINDOW_SECONDS = 60


# ========================================
# REDIS CACHE TTL (seconds)
# ========================================

CACHE_TTL_USER = 300  # 5 minutes
CACHE_TTL_WALLET = 180  # 3 minutes
CACHE_TTL_GAME = 60  # 1 minute
CACHE_TTL_BET = 120  # 2 minutes
CACHE_TTL_STATISTICS = 600  # 10 minutes


# ========================================
# CELERY TASK CONFIGURATION
# ========================================

# Task retry configuration
TASK_MAX_RETRIES = 3
TASK_RETRY_DELAY_SECONDS = 60  # 1 minute

# Periodic task intervals (seconds)
TASK_MATCH_FUNDING_INTERVAL = 300  # 5 minutes
TASK_EXPIRE_REQUESTS_INTERVAL = 600  # 10 minutes
TASK_PROCESS_GAME_RESULTS_INTERVAL = 60  # 1 minute
TASK_UPDATE_STATISTICS_INTERVAL = 900  # 15 minutes


# ========================================
# BETTING ENUMS
# ========================================

class CurrencyType(str, Enum):
    """Currency types"""
    NAIRA = "NAIRA"
    USDT = "USDT"


class BetSide(str, Enum):
    """Bet side options"""
    HOME = "home"
    AWAY = "away"


class BetType(str, Enum):
    """Bet type options"""
    RENDEZVOUS = "rendezvous"
    ONE_V_ONE = "1v1"
    CUSTOM = "custom"


class BetStatus(str, Enum):
    """Bet registration status"""
    ACTIVE = "active"
    WON = "won"
    LOST = "lost"
    CANCELLED = "cancelled"
    PENDING = "pending"


class GameStatus(str, Enum):
    """Game status"""
    UPCOMING = "upcoming"
    LIVE = "live"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class GameResult(str, Enum):
    """Game result options"""
    HOME = "home"
    AWAY = "away"
    DRAW = "draw"


class TransactionType(str, Enum):
    """Transaction types"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    WIN = "win"
    BET_PLACED = "bet_placed"
    BET_REFUND = "bet_refund"
    REFERRAL_BONUS = "referral_bonus"
    PLATFORM_FEE = "platform_fee"


class FundingRequestStatus(str, Enum):
    """Funding request status"""
    PENDING = "pending"
    MATCHED = "matched"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class WithdrawalRequestStatus(str, Enum):
    """Withdrawal request status"""
    PENDING = "pending"
    MATCHED = "matched"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class FundingMatchStatus(str, Enum):
    """Funding match status"""
    MATCHED = "matched"
    PROOF_UPLOADED = "proof_uploaded"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class MatchPairStatus(str, Enum):
    """1v1 match pair status"""
    MATCHED = "matched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BetQueueStatus(str, Enum):
    """1v1 bet queue status"""
    WAITING = "waiting"
    MATCHED = "matched"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# ========================================
# ERROR CODES
# ========================================

class ErrorCode(str, Enum):
    """Standardized error codes"""
    # Authentication (1xxx)
    INVALID_CREDENTIALS = "AUTH_1001"
    INVALID_TOKEN = "AUTH_1002"
    TOKEN_EXPIRED = "AUTH_1003"
    MISSING_TOKEN = "AUTH_1004"

    # Authorization (2xxx)
    INSUFFICIENT_PERMISSIONS = "AUTH_2001"
    ADMIN_REQUIRED = "AUTH_2002"
    ACCOUNT_BLOCKED = "AUTH_2003"

    # Resource Not Found (3xxx)
    USER_NOT_FOUND = "RESOURCE_3001"
    WALLET_NOT_FOUND = "RESOURCE_3002"
    GAME_NOT_FOUND = "RESOURCE_3003"
    BET_NOT_FOUND = "RESOURCE_3004"

    # Validation (4xxx)
    VALIDATION_ERROR = "VALIDATION_4000"
    INVALID_AMOUNT = "VALIDATION_4001"
    INVALID_CURRENCY = "VALIDATION_4002"
    INVALID_BET_SIDE = "VALIDATION_4003"

    # Business Logic (5xxx)
    INSUFFICIENT_BALANCE = "BUSINESS_5001"
    DUPLICATE_REGISTRATION = "BUSINESS_5002"
    BETTING_CLOSED = "BUSINESS_5003"
    GAME_ALREADY_STARTED = "BUSINESS_5004"
    BET_ALREADY_PLACED = "BUSINESS_5005"
    NO_MATCH_FOUND = "BUSINESS_5006"
    CANCELLATION_LIMIT_EXCEEDED = "BUSINESS_5007"

    # Server Errors (9xxx)
    INTERNAL_SERVER_ERROR = "SERVER_9000"
    DATABASE_ERROR = "SERVER_9001"
    EXTERNAL_SERVICE_ERROR = "SERVER_9002"


# ========================================
# HTTP STATUS CODES
# ========================================

HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_204_NO_CONTENT = 204
HTTP_400_BAD_REQUEST = 400
HTTP_401_UNAUTHORIZED = 401
HTTP_403_FORBIDDEN = 403
HTTP_404_NOT_FOUND = 404
HTTP_409_CONFLICT = 409
HTTP_422_UNPROCESSABLE_ENTITY = 422
HTTP_429_TOO_MANY_REQUESTS = 429
HTTP_500_INTERNAL_SERVER_ERROR = 500
HTTP_503_SERVICE_UNAVAILABLE = 503


# ========================================
# LOGGING CONFIGURATION
# ========================================

# Log levels
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"

# Default log level
DEFAULT_LOG_LEVEL = LOG_LEVEL_INFO

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


# ========================================
# TIME ZONES
# ========================================

# Platform timezone (UTC)
PLATFORM_TIMEZONE = "UTC"

# Display timezone for Nigerian users
DISPLAY_TIMEZONE_NIGERIA = "Africa/Lagos"  # WAT (West Africa Time)


# ========================================
# FILE UPLOAD LIMITS
# ========================================

# Maximum file size for proof upload (bytes)
MAX_PROOF_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

# Allowed file types for proof upload
ALLOWED_PROOF_FILE_TYPES = [
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/pdf"
]


# ========================================
# NOTIFICATION SETTINGS
# ========================================

# Email notification settings
EMAIL_NOTIFICATION_ENABLED = True
EMAIL_NOTIFICATION_FROM = "noreply@2-aside.com"

# SMS notification settings
SMS_NOTIFICATION_ENABLED = False  # Disabled by default

# Push notification settings
PUSH_NOTIFICATION_ENABLED = False  # Disabled by default


# ========================================
# ADMIN DASHBOARD
# ========================================

# Statistics refresh interval (seconds)
ADMIN_STATS_REFRESH_INTERVAL = 60  # 1 minute

# Recent activity limit
ADMIN_RECENT_ACTIVITY_LIMIT = 50


# ========================================
# CUSTOM BET SETTINGS
# ========================================

# Maximum custom bet participants
MAX_CUSTOM_BET_PARTICIPANTS = 10

# Custom bet expiration (hours)
CUSTOM_BET_EXPIRATION_HOURS = 48

# Dispute resolution timeout (days)
DISPUTE_RESOLUTION_TIMEOUT_DAYS = 7


# ========================================
# GAME SETTINGS
# ========================================

# Maximum upcoming games to display
MAX_UPCOMING_GAMES_DISPLAY = 50

# Game result verification delay (minutes)
GAME_RESULT_VERIFICATION_DELAY = 15


# ========================================
# DEVELOPMENT/DEBUG FLAGS
# ========================================

# Enable debug mode (should be False in production)
DEBUG_MODE = False

# Enable SQL query logging
LOG_SQL_QUERIES = False

# Enable detailed error responses (disable in production)
DETAILED_ERROR_RESPONSES = False
