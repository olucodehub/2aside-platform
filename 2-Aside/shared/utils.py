"""
2-Aside Platform - Shared Utility Functions
Helper functions for formatting, validation, and common operations
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
import string
import random
import re
from datetime import datetime, timedelta
import hashlib


# ========================================
# DECIMAL & CURRENCY FORMATTING
# ========================================

def round_decimal(value: Decimal, places: int = 2) -> Decimal:
    """
    Round a decimal value to specified decimal places.

    Args:
        value: Decimal value to round
        places: Number of decimal places (default: 2)

    Returns:
        Rounded Decimal value

    Example:
        >>> round_decimal(Decimal("10.567"), 2)
        Decimal('10.57')
    """
    if places < 0:
        raise ValueError("Decimal places must be non-negative")

    quantize_value = Decimal(10) ** -places
    return value.quantize(quantize_value, rounding=ROUND_HALF_UP)


def format_currency(amount: Decimal, currency: str = "NAIRA") -> str:
    """
    Format a decimal amount as currency string.

    Args:
        amount: Decimal amount
        currency: "NAIRA" or "USDT"

    Returns:
        Formatted currency string

    Example:
        >>> format_currency(Decimal("15000.50"), "NAIRA")
        '₦15,000.50'
        >>> format_currency(Decimal("150.50"), "USDT")
        '150.50 USDT'
    """
    rounded = round_decimal(amount, 2)

    if currency.upper() == "NAIRA":
        # Format with Nigerian Naira symbol
        formatted = f"{rounded:,.2f}"
        return f"₦{formatted}"
    elif currency.upper() == "USDT":
        # Format USDT without symbol prefix
        formatted = f"{rounded:,.2f}"
        return f"{formatted} USDT"
    else:
        # Fallback for unknown currency
        return f"{rounded:,.2f} {currency}"


def parse_currency_amount(amount_str: str) -> Decimal:
    """
    Parse a currency string to Decimal amount.

    Args:
        amount_str: String like "₦15,000.50" or "150.50 USDT"

    Returns:
        Decimal amount

    Example:
        >>> parse_currency_amount("₦15,000.50")
        Decimal('15000.50')
    """
    # Remove currency symbols and text
    cleaned = re.sub(r'[₦,\sUSDTNAIRA]', '', amount_str)

    try:
        return Decimal(cleaned)
    except Exception:
        raise ValueError(f"Invalid currency amount: {amount_str}")


# ========================================
# PLATFORM FEE CALCULATIONS
# ========================================

def calculate_platform_fee(profit: Decimal, fee_percentage: Decimal = Decimal("0.05")) -> Decimal:
    """
    Calculate platform fee from profit.

    Args:
        profit: Total profit amount
        fee_percentage: Fee percentage (default: 0.05 = 5%)

    Returns:
        Platform fee amount (rounded to 2 decimal places)

    Example:
        >>> calculate_platform_fee(Decimal("10000"))
        Decimal('500.00')
    """
    fee = profit * fee_percentage
    return round_decimal(fee, 2)


def calculate_user_payout(profit: Decimal, fee_percentage: Decimal = Decimal("0.05")) -> Decimal:
    """
    Calculate user payout after platform fee.

    Args:
        profit: Total profit amount
        fee_percentage: Fee percentage (default: 0.05 = 5%)

    Returns:
        User payout (95% of profit)

    Example:
        >>> calculate_user_payout(Decimal("10000"))
        Decimal('9500.00')
    """
    fee = calculate_platform_fee(profit, fee_percentage)
    payout = profit - fee
    return round_decimal(payout, 2)


def calculate_1v1_payout(bet_amount: Decimal, fee_percentage: Decimal = Decimal("0.05")) -> Decimal:
    """
    Calculate 1v1 bet payout for winner.

    Args:
        bet_amount: Amount user bet
        fee_percentage: Fee percentage (default: 0.05 = 5%)

    Returns:
        Winner's payout (~1.9x bet amount)

    Example:
        >>> calculate_1v1_payout(Decimal("5000"))
        Decimal('9500.00')
    """
    total_pool = bet_amount * 2  # Both users' bets
    fee = calculate_platform_fee(total_pool, fee_percentage)
    payout = total_pool - fee
    return round_decimal(payout, 2)


def calculate_rendezvous_share(
    user_bet: Decimal,
    total_winning_stake: Decimal,
    total_losing_stake: Decimal,
    fee_percentage: Decimal = Decimal("0.05")
) -> Decimal:
    """
    Calculate individual user's share in Rendezvous (group) betting.

    Args:
        user_bet: User's bet amount
        total_winning_stake: Total amount bet on winning side
        total_losing_stake: Total amount bet on losing side
        fee_percentage: Platform fee percentage (default: 0.05)

    Returns:
        User's payout amount

    Example:
        User bet ₦5,000 on winning side
        Total winning: ₦50,000
        Total losing: ₦30,000

        >>> calculate_rendezvous_share(Decimal("5000"), Decimal("50000"), Decimal("30000"))
        Decimal('7850.00')

        Explanation:
        - Platform fee: 30,000 * 0.05 = ₦1,500
        - Winnings pool: 30,000 - 1,500 = ₦28,500
        - Total distribution: 50,000 + 28,500 = ₦78,500
        - User's share: 78,500 * (5,000 / 50,000) = ₦7,850
    """
    if total_winning_stake == 0:
        return Decimal("0")

    # Calculate platform fee from losing side
    platform_fee = calculate_platform_fee(total_losing_stake, fee_percentage)

    # Winnings pool after fee
    winnings_pool = total_losing_stake - platform_fee

    # Total distribution (original stakes + winnings)
    total_distribution = total_winning_stake + winnings_pool

    # User's proportional share
    share_percentage = user_bet / total_winning_stake
    user_payout = total_distribution * share_percentage

    return round_decimal(user_payout, 2)


# ========================================
# REFERRAL CODE GENERATION
# ========================================

def generate_referral_code(length: int = 8) -> str:
    """
    Generate a unique referral code.

    Args:
        length: Length of the code (default: 8)

    Returns:
        Random alphanumeric referral code (uppercase)

    Example:
        >>> generate_referral_code()
        'A7K9M2X5'
    """
    characters = string.ascii_uppercase + string.digits
    code = ''.join(random.choices(characters, k=length))
    return code


def validate_referral_code(code: str) -> bool:
    """
    Validate referral code format.

    Args:
        code: Referral code to validate

    Returns:
        True if valid format, False otherwise

    Example:
        >>> validate_referral_code("A7K9M2X5")
        True
        >>> validate_referral_code("invalid!")
        False
    """
    if not code:
        return False

    # Must be 6-12 characters, alphanumeric only
    if not re.match(r'^[A-Z0-9]{6,12}$', code.upper()):
        return False

    return True


# ========================================
# DATE & TIME UTILITIES
# ========================================

def get_betting_close_time(game_time: datetime, hours_before: int = 1) -> datetime:
    """
    Calculate betting close time (X hours before game).

    Args:
        game_time: Scheduled game time
        hours_before: Hours before game to close betting (default: 1)

    Returns:
        Betting close datetime

    Example:
        >>> game_time = datetime(2025, 1, 25, 15, 0)
        >>> get_betting_close_time(game_time)
        datetime(2025, 1, 25, 14, 0)
    """
    return game_time - timedelta(hours=hours_before)


def is_betting_open(game_time: datetime, current_time: Optional[datetime] = None) -> bool:
    """
    Check if betting is still open for a game.

    Args:
        game_time: Scheduled game time
        current_time: Current time (default: now)

    Returns:
        True if betting is open, False if closed
    """
    if current_time is None:
        current_time = datetime.utcnow()

    betting_closes = get_betting_close_time(game_time)
    return current_time < betting_closes


def format_datetime_display(dt: datetime) -> str:
    """
    Format datetime for display in UI.

    Args:
        dt: Datetime to format

    Returns:
        Formatted string

    Example:
        >>> dt = datetime(2025, 1, 25, 15, 30)
        >>> format_datetime_display(dt)
        'Jan 25, 2025 at 3:30 PM'
    """
    return dt.strftime("%b %d, %Y at %I:%M %p")


def parse_datetime_from_string(date_str: str) -> Optional[datetime]:
    """
    Parse datetime from various string formats.

    Args:
        date_str: Date string to parse

    Returns:
        Parsed datetime or None if invalid

    Supports formats:
        - ISO 8601: "2025-01-25T15:30:00"
        - "2025-01-25 15:30:00"
        - "25/01/2025 15:30"
    """
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


# ========================================
# VALIDATION UTILITIES
# ========================================

def validate_email(email: str) -> bool:
    """
    Validate email format.

    Args:
        email: Email address to validate

    Returns:
        True if valid format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.

    Args:
        phone: Phone number to validate

    Returns:
        True if valid format, False otherwise
    """
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)

    # Must be 10-15 digits, optionally starting with +
    pattern = r'^\+?[0-9]{10,15}$'
    return bool(re.match(pattern, cleaned))


def validate_uuid(uuid_str: str) -> bool:
    """
    Validate UUID format.

    Args:
        uuid_str: UUID string to validate

    Returns:
        True if valid UUID format, False otherwise
    """
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_str.lower()))


def sanitize_input(text: str, max_length: int = 255) -> str:
    """
    Sanitize user input by removing dangerous characters.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized text
    """
    if not text:
        return ""

    # Remove leading/trailing whitespace
    sanitized = text.strip()

    # Truncate to max length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)

    return sanitized


# ========================================
# HASHING & ENCODING
# ========================================

def generate_transaction_reference(wallet_id: str, timestamp: Optional[datetime] = None) -> str:
    """
    Generate a unique transaction reference.

    Args:
        wallet_id: Wallet UUID
        timestamp: Transaction timestamp (default: now)

    Returns:
        Unique transaction reference

    Example:
        >>> generate_transaction_reference("wallet-123")
        'TXN-A7K9M2X5'
    """
    if timestamp is None:
        timestamp = datetime.utcnow()

    # Create hash from wallet_id + timestamp
    hash_input = f"{wallet_id}{timestamp.isoformat()}".encode('utf-8')
    hash_output = hashlib.sha256(hash_input).hexdigest()[:8].upper()

    return f"TXN-{hash_output}"


def generate_proof_hash(proof_data: str) -> str:
    """
    Generate hash of proof data for verification.

    Args:
        proof_data: Proof data to hash

    Returns:
        SHA-256 hash
    """
    return hashlib.sha256(proof_data.encode('utf-8')).hexdigest()


# ========================================
# PAGINATION HELPERS
# ========================================

def calculate_pagination(page: int, per_page: int, total_items: int) -> dict:
    """
    Calculate pagination metadata.

    Args:
        page: Current page number (1-indexed)
        per_page: Items per page
        total_items: Total number of items

    Returns:
        Dictionary with pagination metadata

    Example:
        >>> calculate_pagination(2, 20, 150)
        {
            'page': 2,
            'per_page': 20,
            'total_items': 150,
            'total_pages': 8,
            'has_next': True,
            'has_prev': True,
            'offset': 20
        }
    """
    total_pages = (total_items + per_page - 1) // per_page  # Ceiling division

    return {
        'page': page,
        'per_page': per_page,
        'total_items': total_items,
        'total_pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'offset': (page - 1) * per_page
    }


def get_offset_limit(page: int, per_page: int) -> tuple[int, int]:
    """
    Calculate SQL offset and limit from page number.

    Args:
        page: Current page number (1-indexed)
        per_page: Items per page

    Returns:
        Tuple of (offset, limit)

    Example:
        >>> get_offset_limit(3, 20)
        (40, 20)
    """
    offset = (page - 1) * per_page
    limit = per_page
    return offset, limit


# ========================================
# ERROR FORMATTING
# ========================================

def format_validation_error(errors: list) -> str:
    """
    Format Pydantic validation errors into readable message.

    Args:
        errors: List of validation error dicts from Pydantic

    Returns:
        Formatted error message
    """
    messages = []
    for error in errors:
        field = " -> ".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Unknown error")
        messages.append(f"{field}: {message}")

    return "; ".join(messages)


def safe_divide(numerator: Decimal, denominator: Decimal, default: Decimal = Decimal("0")) -> Decimal:
    """
    Safely divide two decimals, returning default if denominator is zero.

    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if denominator is zero

    Returns:
        Division result or default
    """
    if denominator == 0:
        return default

    return round_decimal(numerator / denominator, 2)
