"""
2-Aside Platform - Custom Exception Classes
Standardized exceptions for error handling across all microservices
"""

from typing import Optional, Any


# ========================================
# BASE EXCEPTION CLASSES
# ========================================

class TwoAsideBaseException(Exception):
    """Base exception for all 2-Aside custom exceptions"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: int = 500,
        detail: Optional[Any] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses"""
        return {
            "success": False,
            "error": self.message,
            "error_code": self.error_code,
            "detail": self.detail
        }


# ========================================
# AUTHENTICATION EXCEPTIONS (401)
# ========================================

class AuthenticationError(TwoAsideBaseException):
    """Base authentication error"""

    def __init__(self, message: str = "Authentication failed", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR",
            status_code=401,
            detail=detail
        )


class InvalidCredentialsError(AuthenticationError):
    """Invalid email or password"""

    def __init__(self, message: str = "Invalid email or password"):
        super().__init__(message=message)
        self.error_code = "INVALID_CREDENTIALS"


class InvalidTokenError(AuthenticationError):
    """Invalid or expired JWT token"""

    def __init__(self, message: str = "Invalid or expired token"):
        super().__init__(message=message)
        self.error_code = "INVALID_TOKEN"


class TokenExpiredError(AuthenticationError):
    """JWT token has expired"""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message=message)
        self.error_code = "TOKEN_EXPIRED"


class MissingTokenError(AuthenticationError):
    """No authentication token provided"""

    def __init__(self, message: str = "Authentication token required"):
        super().__init__(message=message)
        self.error_code = "MISSING_TOKEN"


# ========================================
# AUTHORIZATION EXCEPTIONS (403)
# ========================================

class AuthorizationError(TwoAsideBaseException):
    """Base authorization error"""

    def __init__(self, message: str = "Access denied", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="AUTH_FORBIDDEN",
            status_code=403,
            detail=detail
        )


class InsufficientPermissionsError(AuthorizationError):
    """User lacks required permissions"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message)
        self.error_code = "INSUFFICIENT_PERMISSIONS"


class AdminRequiredError(AuthorizationError):
    """Admin privileges required"""

    def __init__(self, message: str = "Admin privileges required"):
        super().__init__(message=message)
        self.error_code = "ADMIN_REQUIRED"


class AccountBlockedError(AuthorizationError):
    """User account is blocked"""

    def __init__(
        self,
        message: str = "Your account has been blocked",
        reason: Optional[str] = None
    ):
        super().__init__(
            message=message,
            detail={"reason": reason} if reason else None
        )
        self.error_code = "ACCOUNT_BLOCKED"


# ========================================
# RESOURCE NOT FOUND EXCEPTIONS (404)
# ========================================

class ResourceNotFoundError(TwoAsideBaseException):
    """Base resource not found error"""

    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        message: Optional[str] = None
    ):
        if message is None:
            message = f"{resource_type} not found"
            if resource_id:
                message += f": {resource_id}"

        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            detail={"resource_type": resource_type, "resource_id": resource_id}
        )


class UserNotFoundError(ResourceNotFoundError):
    """User not found"""

    def __init__(self, user_id: Optional[str] = None):
        super().__init__(
            resource_type="User",
            resource_id=user_id,
            message="User not found"
        )


class WalletNotFoundError(ResourceNotFoundError):
    """Wallet not found"""

    def __init__(self, wallet_id: Optional[str] = None):
        super().__init__(
            resource_type="Wallet",
            resource_id=wallet_id,
            message="Wallet not found"
        )


class GameNotFoundError(ResourceNotFoundError):
    """Game not found"""

    def __init__(self, game_id: Optional[str] = None):
        super().__init__(
            resource_type="Game",
            resource_id=game_id,
            message="Game not found"
        )


class BetNotFoundError(ResourceNotFoundError):
    """Bet registration not found"""

    def __init__(self, bet_id: Optional[str] = None):
        super().__init__(
            resource_type="Bet",
            resource_id=bet_id,
            message="Bet not found"
        )


class FundingRequestNotFoundError(ResourceNotFoundError):
    """Funding request not found"""

    def __init__(self, request_id: Optional[str] = None):
        super().__init__(
            resource_type="FundingRequest",
            resource_id=request_id,
            message="Funding request not found"
        )


# ========================================
# VALIDATION EXCEPTIONS (400)
# ========================================

class ValidationError(TwoAsideBaseException):
    """Base validation error"""

    def __init__(
        self,
        message: str = "Validation failed",
        field: Optional[str] = None,
        detail: Optional[Any] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            detail={"field": field, "detail": detail} if field else detail
        )


class InvalidAmountError(ValidationError):
    """Invalid amount value"""

    def __init__(self, message: str = "Invalid amount", minimum: Optional[float] = None):
        detail = {"minimum": minimum} if minimum else None
        super().__init__(
            message=message,
            field="amount",
            detail=detail
        )


class InvalidCurrencyError(ValidationError):
    """Invalid currency type"""

    def __init__(self, currency: Optional[str] = None):
        message = f"Invalid currency: {currency}" if currency else "Invalid currency"
        super().__init__(
            message=message,
            field="currency"
        )


class InvalidBetSideError(ValidationError):
    """Invalid bet side"""

    def __init__(self, side: Optional[str] = None):
        message = f"Invalid bet side: {side}" if side else "Invalid bet side (must be 'home' or 'away')"
        super().__init__(
            message=message,
            field="side"
        )


class InvalidReferralCodeError(ValidationError):
    """Invalid referral code format"""

    def __init__(self, code: Optional[str] = None):
        message = f"Invalid referral code: {code}" if code else "Invalid referral code"
        super().__init__(
            message=message,
            field="referral_code"
        )


# ========================================
# BUSINESS LOGIC EXCEPTIONS (400)
# ========================================

class BusinessLogicError(TwoAsideBaseException):
    """Base business logic error"""

    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            status_code=400,
            detail=detail
        )


class InsufficientBalanceError(BusinessLogicError):
    """Insufficient wallet balance"""

    def __init__(
        self,
        message: str = "Insufficient balance",
        required: Optional[float] = None,
        available: Optional[float] = None
    ):
        detail = None
        if required is not None and available is not None:
            detail = {"required": required, "available": available}

        super().__init__(
            message=message,
            detail=detail
        )


class DuplicateRegistrationError(BusinessLogicError):
    """User already registered (duplicate email/username)"""

    def __init__(self, field: str = "email"):
        super().__init__(
            message=f"This {field} is already registered",
            detail={"field": field}
        )


class BettingClosedError(BusinessLogicError):
    """Betting window has closed for this game"""

    def __init__(self, game_id: Optional[str] = None):
        super().__init__(
            message="Betting is closed for this game",
            detail={"game_id": game_id} if game_id else None
        )


class GameAlreadyStartedError(BusinessLogicError):
    """Game has already started"""

    def __init__(self, game_id: Optional[str] = None):
        super().__init__(
            message="This game has already started",
            detail={"game_id": game_id} if game_id else None
        )


class GameAlreadyFinishedError(BusinessLogicError):
    """Game has already finished"""

    def __init__(self, game_id: Optional[str] = None):
        super().__init__(
            message="This game has already finished",
            detail={"game_id": game_id} if game_id else None
        )


class BetAlreadyPlacedError(BusinessLogicError):
    """User already has a bet on this game"""

    def __init__(self, game_id: Optional[str] = None):
        super().__init__(
            message="You have already placed a bet on this game",
            detail={"game_id": game_id} if game_id else None
        )


class NoMatchFoundError(BusinessLogicError):
    """No matching bet found for 1v1 pairing"""

    def __init__(self):
        super().__init__(
            message="No matching bet found. Your bet has been added to the queue."
        )


class MatchAlreadyExistsError(BusinessLogicError):
    """1v1 match already exists for this bet"""

    def __init__(self):
        super().__init__(
            message="This bet is already matched"
        )


class WithdrawalExceedsBalanceError(BusinessLogicError):
    """Withdrawal amount exceeds available balance"""

    def __init__(self, requested: Optional[float] = None, available: Optional[float] = None):
        message = "Withdrawal amount exceeds available balance"
        detail = None
        if requested is not None and available is not None:
            detail = {"requested": requested, "available": available}

        super().__init__(message=message, detail=detail)


class FundingNotMatchedError(BusinessLogicError):
    """Funding request not yet matched with a withdrawal"""

    def __init__(self):
        super().__init__(
            message="This funding request has not been matched yet"
        )


class ProofAlreadyUploadedError(BusinessLogicError):
    """Proof already uploaded for this funding match"""

    def __init__(self):
        super().__init__(
            message="Proof has already been uploaded for this match"
        )


class ProofNotUploadedError(BusinessLogicError):
    """Proof not yet uploaded"""

    def __init__(self):
        super().__init__(
            message="Proof of payment has not been uploaded yet"
        )


class SelfReferralError(BusinessLogicError):
    """User cannot refer themselves"""

    def __init__(self):
        super().__init__(
            message="You cannot use your own referral code"
        )


class ReferralAlreadyUsedError(BusinessLogicError):
    """User has already used a referral code"""

    def __init__(self):
        super().__init__(
            message="You have already used a referral code"
        )


class CancellationLimitExceededError(BusinessLogicError):
    """User exceeded max consecutive cancellations"""

    def __init__(self, limit: int = 3):
        super().__init__(
            message=f"You have exceeded the maximum consecutive cancellations ({limit})",
            detail={"limit": limit}
        )


class MissedPaymentLimitExceededError(BusinessLogicError):
    """User exceeded max consecutive missed payments"""

    def __init__(self, limit: int = 3):
        super().__init__(
            message=f"You have exceeded the maximum consecutive missed payments ({limit})",
            detail={"limit": limit}
        )


# ========================================
# CONFLICT EXCEPTIONS (409)
# ========================================

class ConflictError(TwoAsideBaseException):
    """Base conflict error"""

    def __init__(self, message: str, detail: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="CONFLICT_ERROR",
            status_code=409,
            detail=detail
        )


class WalletAlreadyExistsError(ConflictError):
    """Wallet already exists for this currency"""

    def __init__(self, currency: str):
        super().__init__(
            message=f"Wallet already exists for currency: {currency}",
            detail={"currency": currency}
        )


class OperationInProgressError(ConflictError):
    """Another operation is in progress"""

    def __init__(self, operation: str):
        super().__init__(
            message=f"Operation in progress: {operation}",
            detail={"operation": operation}
        )


# ========================================
# RATE LIMIT EXCEPTIONS (429)
# ========================================

class RateLimitExceededError(TwoAsideBaseException):
    """Rate limit exceeded"""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please try again later.",
        retry_after: Optional[int] = None
    ):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            status_code=429,
            detail={"retry_after": retry_after} if retry_after else None
        )


# ========================================
# SERVER EXCEPTIONS (500)
# ========================================

class InternalServerError(TwoAsideBaseException):
    """Internal server error"""

    def __init__(self, message: str = "An internal error occurred", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code="INTERNAL_SERVER_ERROR",
            status_code=500,
            detail=detail
        )


class DatabaseError(InternalServerError):
    """Database operation failed"""

    def __init__(self, message: str = "Database operation failed", detail: Optional[Any] = None):
        super().__init__(
            message=message,
            detail=detail
        )


class ExternalServiceError(InternalServerError):
    """External service unavailable or failed"""

    def __init__(self, service_name: str, detail: Optional[Any] = None):
        super().__init__(
            message=f"External service unavailable: {service_name}",
            detail=detail
        )


# ========================================
# SERVICE UNAVAILABLE EXCEPTIONS (503)
# ========================================

class ServiceUnavailableError(TwoAsideBaseException):
    """Service temporarily unavailable"""

    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            status_code=503
        )


class MaintenanceModeError(ServiceUnavailableError):
    """Platform under maintenance"""

    def __init__(self):
        super().__init__(
            message="Platform is currently under maintenance. Please try again later."
        )
