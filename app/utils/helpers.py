# ============================================================
# AETHER LINK - HELPERS
# ============================================================

import secrets
import string
import re
import uuid
from datetime import datetime
from typing import Optional, Any, Dict, List, Union
from decimal import Decimal, ROUND_HALF_UP

# ============================================================
# CONSTANTS
# ============================================================

# Default random string length
DEFAULT_RANDOM_LENGTH = 32

# Currency configurations
CURRENCIES = {
    'PKR': {
        'symbol': '₨',
        'code': 'PKR',
        'decimal_places': 2,
        'thousands_separator': ',',
        'decimal_separator': '.',
    },
    'USD': {
        'symbol': '$',
        'code': 'USD',
        'decimal_places': 2,
        'thousands_separator': ',',
        'decimal_separator': '.',
    },
    'EUR': {
        'symbol': '€',
        'code': 'EUR',
        'decimal_places': 2,
        'thousands_separator': ',',
        'decimal_separator': '.',
    },
    'GBP': {
        'symbol': '£',
        'code': 'GBP',
        'decimal_places': 2,
        'thousands_separator': ',',
        'decimal_separator': '.',
    },
}


# ============================================================
# RANDOM STRING GENERATION
# ============================================================

def generate_random_string(length: int = DEFAULT_RANDOM_LENGTH) -> str:
    """
    Generate a cryptographically secure random string.
    
    Args:
        length: Length of the string (default: 32)
    
    Returns:
        Random string containing letters and digits
    
    Examples:
        >>> generate_random_string(10)
        "aB3xY7pQ9m"
    """
    if length < 1:
        length = 1
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_secure_token(length: int = 64) -> str:
    """
    Generate a secure token (hexadecimal).
    
    Args:
        length: Length of the token (default: 64)
    
    Returns:
        Hexadecimal token
    
    Examples:
        >>> generate_secure_token(32)
        "a1b2c3d4e5f67890..."
    """
    return secrets.token_hex(length // 2)


def generate_verification_code(length: int = 6) -> str:
    """
    Generate a numeric verification code.
    
    Args:
        length: Length of the code (default: 6)
    
    Returns:
        Numeric code as string
    
    Examples:
        >>> generate_verification_code(6)
        "123456"
    """
    if length < 1:
        length = 1
    
    # First digit cannot be 0
    first = str(secrets.randbelow(9) + 1)
    rest = ''.join(str(secrets.randbelow(10)) for _ in range(length - 1))
    return first + rest


def generate_random_password(length: int = 12) -> str:
    """
    Generate a secure random password.
    
    Args:
        length: Length of the password (default: 12)
    
    Returns:
        Password with letters, digits, and special characters
    
    Examples:
        >>> generate_random_password(12)
        "aB3xY7pQ9m!@"
    """
    if length < 8:
        length = 8
    
    # Ensure at least one of each type
    lowercase = secrets.choice(string.ascii_lowercase)
    uppercase = secrets.choice(string.ascii_uppercase)
    digit = secrets.choice(string.digits)
    special = secrets.choice('!@#$%^&*')
    
    # Fill the rest with random characters
    remaining = length - 4
    all_chars = string.ascii_letters + string.digits + '!@#$%^&*'
    rest = ''.join(secrets.choice(all_chars) for _ in range(remaining))
    
    # Combine and shuffle
    password = list(lowercase + uppercase + digit + special + rest)
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


# ============================================================
# SLUG GENERATION
# ============================================================

def generate_slug(text: str, max_length: int = 255) -> str:
    """
    Generate a URL-friendly slug from text.
    
    Args:
        text: Text to convert to slug
        max_length: Maximum slug length
    
    Returns:
        URL-friendly slug
    
    Examples:
        >>> generate_slug("Hello World!")
        "hello-world"
        
        >>> generate_slug("Aether Link Course")
        "aether-link-course"
    """
    if not text:
        return ""
    
    # Convert to lowercase and remove accents (basic)
    text = text.lower()
    
    # Replace spaces and special characters with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Remove consecutive hyphens
    text = re.sub(r'-+', '-', text)
    
    # Truncate
    if len(text) > max_length:
        text = text[:max_length]
        text = re.sub(r'-[^-]*$', '', text)  # Remove incomplete last word
    
    return text or "untitled"


def generate_unique_slug(base_text: str, existing_slugs: List[str], max_length: int = 255) -> str:
    """
    Generate a unique slug by checking against existing slugs.
    
    Args:
        base_text: Base text for slug
        existing_slugs: List of existing slugs to check against
        max_length: Maximum slug length
    
    Returns:
        Unique slug
    
    Examples:
        >>> generate_unique_slug("Course", ["course"])
        "course-1"
        
        >>> generate_unique_slug("Course", ["course", "course-1"])
        "course-2"
    """
    base_slug = generate_slug(base_text, max_length)
    
    if not base_slug:
        base_slug = "untitled"
    
    # If slug doesn't exist, return it
    if base_slug not in existing_slugs:
        return base_slug
    
    # Otherwise, append a number
    counter = 1
    while True:
        new_slug = f"{base_slug}-{counter}"
        if new_slug not in existing_slugs:
            return new_slug
        counter += 1


# ============================================================
# TEXT UTILITIES
# ============================================================

def truncate_text(text: str, max_length: int = 200, suffix: str = '...') -> str:
    """
    Truncate text to specified length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add (default: '...')
    
    Returns:
        Truncated text
    
    Examples:
        >>> truncate_text("This is a long text", 10)
        "This is..."
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # Truncate at word boundary if possible
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        truncated = truncated[:last_space]
    
    return truncated + suffix


def extract_text_from_html(html_content: str) -> str:
    """
    Extract plain text from HTML content.
    
    Args:
        html_content: HTML content
    
    Returns:
        Plain text
    
    Examples:
        >>> extract_text_from_html("<p>Hello <b>World</b></p>")
        "Hello World"
    """
    if not html_content:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', html_content)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def slugify(text: str) -> str:
    """
    Alias for generate_slug.
    """
    return generate_slug(text)


# ============================================================
# CURRENCY FORMATTING
# ============================================================

def format_currency(
    amount: Union[float, Decimal, int],
    currency: str = 'PKR',
    include_symbol: bool = True,
    include_code: bool = False
) -> str:
    """
    Format amount as currency.
    
    Args:
        amount: Amount to format
        currency: Currency code (PKR, USD, EUR, GBP)
        include_symbol: Include currency symbol
        include_code: Include currency code
    
    Returns:
        Formatted currency string
    
    Examples:
        >>> format_currency(1500.50, "PKR")
        "₨ 1,500.50"
        
        >>> format_currency(100.00, "USD")
        "$ 100.00"
        
        >>> format_currency(99.99, "USD", include_code=True)
        "$ 99.99 USD"
    """
    if amount is None:
        return ""
    
    # Convert to Decimal for precise formatting
    if isinstance(amount, (int, float)):
        amount = Decimal(str(amount))
    
    # Get currency config
    config = CURRENCIES.get(currency.upper(), CURRENCIES['PKR'])
    
    # Round to decimal places
    decimal_places = config['decimal_places']
    amount = amount.quantize(Decimal('0.1') ** decimal_places, rounding=ROUND_HALF_UP)
    
    # Format number with thousands separator
    amount_str = f"{amount:,.{decimal_places}f}"
    amount_str = amount_str.replace(',', config['thousands_separator'])
    amount_str = amount_str.replace('.', config['decimal_separator'])
    
    # Build final string
    parts = []
    
    if include_symbol:
        parts.append(config['symbol'])
    
    parts.append(amount_str)
    
    if include_code:
        parts.append(config['code'])
    
    return ' '.join(parts)


def format_currency_pkr(amount: Union[float, Decimal, int]) -> str:
    """Format amount as PKR currency."""
    return format_currency(amount, 'PKR')


def format_currency_usd(amount: Union[float, Decimal, int]) -> str:
    """Format amount as USD currency."""
    return format_currency(amount, 'USD')


# ============================================================
# DATE & TIME FORMATTING
# ============================================================

def format_datetime(
    dt: Optional[datetime],
    format_str: str = '%Y-%m-%d %H:%M:%S'
) -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
    
    Returns:
        Formatted datetime string
    
    Examples:
        >>> format_datetime(datetime(2024, 1, 1, 12, 0, 0))
        "2024-01-01 12:00:00"
    """
    if dt is None:
        return ""
    return dt.strftime(format_str)


def format_date(
    dt: Optional[datetime],
    format_str: str = '%Y-%m-%d'
) -> str:
    """
    Format date to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
    
    Returns:
        Formatted date string
    
    Examples:
        >>> format_date(datetime(2024, 1, 1))
        "2024-01-01"
    """
    if dt is None:
        return ""
    return dt.strftime(format_str)


def format_time(
    dt: Optional[datetime],
    format_str: str = '%H:%M:%S'
) -> str:
    """
    Format time to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
    
    Returns:
        Formatted time string
    
    Examples:
        >>> format_time(datetime(2024, 1, 1, 12, 0, 0))
        "12:00:00"
    """
    if dt is None:
        return ""
    return dt.strftime(format_str)


# ============================================================
# SAFE CONVERSIONS
# ============================================================

def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert to integer.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Integer value or default
    
    Examples:
        >>> safe_int("123")
        123
        
        >>> safe_int("abc")
        0
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert to float.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Float value or default
    
    Examples:
        >>> safe_float("123.45")
        123.45
        
        >>> safe_float("abc")
        0.0
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """
    Safely convert to string.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        String value or default
    """
    if value is None:
        return default
    try:
        return str(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """
    Safely convert to boolean.
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
    
    Returns:
        Boolean value or default
    
    Examples:
        >>> safe_bool("true")
        True
        
        >>> safe_bool("false")
        False
        
        >>> safe_bool("yes")
        True
    """
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower in ('true', 'yes', '1', 'on', 'active', 'enabled'):
            return True
        if value_lower in ('false', 'no', '0', 'off', 'inactive', 'disabled'):
            return False
    
    try:
        return bool(value)
    except (ValueError, TypeError):
        return default


# ============================================================
# NESTED DATA ACCESS
# ============================================================

def get_nested_value(data: Dict, keys: List[str], default: Any = None) -> Any:
    """
    Safely get nested dictionary value.
    
    Args:
        data: Dictionary to search
        keys: List of keys to traverse
        default: Default value if not found
    
    Returns:
        Value or default
    
    Examples:
        >>> data = {"user": {"profile": {"name": "John"}}}
        >>> get_nested_value(data, ["user", "profile", "name"])
        "John"
        
        >>> get_nested_value(data, ["user", "email"])
        None
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    return current


def has_nested_key(data: Dict, keys: List[str]) -> bool:
    """
    Check if nested key exists in dictionary.
    
    Args:
        data: Dictionary to check
        keys: List of keys to traverse
    
    Returns:
        True if key exists
    
    Examples:
        >>> data = {"user": {"profile": {"name": "John"}}}
        >>> has_nested_key(data, ["user", "profile", "name"])
        True
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return False
    return True


# ============================================================
# UUID VALIDATION
# ============================================================

def is_valid_uuid(uuid_string: str, version: int = 4) -> bool:
    """
    Check if string is a valid UUID.
    
    Args:
        uuid_string: String to check
        version: UUID version (4 by default)
    
    Returns:
        True if valid UUID
    
    Examples:
        >>> is_valid_uuid("123e4567-e89b-12d3-a456-426614174000")
        True
        
        >>> is_valid_uuid("invalid-uuid")
        False
    """
    try:
        uuid_obj = uuid.UUID(uuid_string)
        return str(uuid_obj) == uuid_string and uuid_obj.version == version
    except (ValueError, TypeError, AttributeError):
        return False


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Random generation
    'generate_random_string',
    'generate_secure_token',
    'generate_verification_code',
    'generate_random_password',
    
    # Slug generation
    'generate_slug',
    'generate_unique_slug',
    'slugify',
    
    # Text utilities
    'truncate_text',
    'extract_text_from_html',
    
    # Currency formatting
    'format_currency',
    'format_currency_pkr',
    'format_currency_usd',
    
    # Date formatting
    'format_datetime',
    'format_date',
    'format_time',
    
    # Safe conversions
    'safe_int',
    'safe_float',
    'safe_str',
    'safe_bool',
    
    # Nested data
    'get_nested_value',
    'has_nested_key',
    
    # UUID
    'is_valid_uuid',
]