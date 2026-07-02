# ============================================================
# AETHER LINK - SLUG GENERATOR
# ============================================================

import re
import unicodedata
from typing import Optional, List, Set
import string

# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_MAX_LENGTH = 255
DEFAULT_SEPARATOR = '-'
DEFAULT_EMPTY_SLUG = 'untitled'

# Characters allowed in slugs
ALLOWED_CHARS = string.ascii_lowercase + string.digits + DEFAULT_SEPARATOR

# Common words to remove from slugs (optional)
STOP_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'for', 'nor', 'on', 'at', 'to', 'by', 'in', 'of'
}


# ============================================================
# CORE SLUG GENERATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize text by removing accents and converting to ASCII.
    
    Args:
        text: Text to normalize
    
    Returns:
        Normalized text
    
    Examples:
        >>> normalize_text("Café")
        "Cafe"
        
        >>> normalize_text("ñandú")
        "nandu"
    """
    if not text:
        return ""
    
    # Normalize unicode (NFKD decomposes characters)
    normalized = unicodedata.normalize('NFKD', text)
    
    # Encode to ASCII and decode back (removes accents)
    normalized = normalized.encode('ascii', 'ignore').decode('ascii')
    
    return normalized


def clean_text_for_slug(text: str) -> str:
    """
    Clean text for slug generation.
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text
    
    Examples:
        >>> clean_text_for_slug("  Hello   World!  ")
        "hello-world"
        
        >>> clean_text_for_slug("Aether Link Course 2024")
        "aether-link-course-2024"
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Normalize unicode
    text = normalize_text(text)
    
    # Replace special characters with spaces
    # Keep only letters, numbers, and spaces
    text = re.sub(r'[^a-z0-9\s\-]', ' ', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing spaces
    text = text.strip()
    
    return text


def generate_slug(
    text: str,
    max_length: int = DEFAULT_MAX_LENGTH,
    separator: str = DEFAULT_SEPARATOR,
    stop_words: Optional[Set[str]] = None,
) -> str:
    """
    Generate a URL-friendly slug from text.
    
    Args:
        text: Text to convert to slug
        max_length: Maximum slug length
        separator: Separator character (default: '-')
        stop_words: Set of words to remove (optional)
    
    Returns:
        URL-friendly slug
    
    Examples:
        >>> generate_slug("Hello World!")
        "hello-world"
        
        >>> generate_slug("  Aether Link   Course  ")
        "aether-link-course"
        
        >>> generate_slug("Café & Bakery")
        "cafe-bakery"
    """
    if not text:
        return DEFAULT_EMPTY_SLUG
    
    # Clean text
    cleaned = clean_text_for_slug(text)
    
    if not cleaned:
        return DEFAULT_EMPTY_SLUG
    
    # Remove stop words (optional)
    if stop_words:
        words = cleaned.split()
        cleaned = ' '.join(word for word in words if word not in stop_words)
    
    # Replace spaces with separator
    slug = cleaned.replace(' ', separator)
    
    # Remove consecutive separators
    slug = re.sub(r'\-+', separator, slug)
    
    # Remove leading/trailing separators
    slug = slug.strip(separator)
    
    # Truncate if too long
    if len(slug) > max_length:
        slug = slug[:max_length]
        # Remove incomplete last word
        slug = re.sub(r'\-[^-]*$', '', slug)
    
    return slug or DEFAULT_EMPTY_SLUG


def generate_unique_slug(
    base_text: str,
    existing_slugs: List[str],
    max_length: int = DEFAULT_MAX_LENGTH,
    separator: str = DEFAULT_SEPARATOR,
) -> str:
    """
    Generate a unique slug by checking against existing slugs.
    
    Args:
        base_text: Base text for slug
        existing_slugs: List of existing slugs to check against
        max_length: Maximum slug length
        separator: Separator character
    
    Returns:
        Unique slug
    
    Examples:
        >>> generate_unique_slug("Course", ["course"])
        "course-1"
        
        >>> generate_unique_slug("Course", ["course", "course-1"])
        "course-2"
        
        >>> generate_unique_slug("Course", [])
        "course"
    """
    # Generate base slug
    base_slug = generate_slug(base_text, max_length, separator)
    
    if not base_slug:
        base_slug = DEFAULT_EMPTY_SLUG
    
    # If no existing slugs or slug is unique, return it
    if not existing_slugs or base_slug not in existing_slugs:
        return base_slug
    
    # Otherwise, append a number
    counter = 1
    while True:
        new_slug = f"{base_slug}{separator}{counter}"
        
        # Ensure we don't exceed max length
        if len(new_slug) > max_length:
            # Truncate base and try again
            base_slug = base_slug[:max_length - len(f"{separator}{counter}") - 1]
            new_slug = f"{base_slug}{separator}{counter}"
        
        if new_slug not in existing_slugs:
            return new_slug
        
        counter += 1


def generate_slug_from_title(
    title: str,
    existing_slugs: Optional[List[str]] = None,
    max_length: int = DEFAULT_MAX_LENGTH,
) -> str:
    """
    Generate slug from title with duplicate handling.
    
    Args:
        title: Title to generate slug from
        existing_slugs: List of existing slugs (optional)
        max_length: Maximum slug length
    
    Returns:
        Unique slug
    
    Examples:
        >>> generate_slug_from_title("My Course")
        "my-course"
        
        >>> generate_slug_from_title("My Course", ["my-course"])
        "my-course-1"
    """
    if existing_slugs:
        return generate_unique_slug(title, existing_slugs, max_length)
    
    return generate_slug(title, max_length)


# ============================================================
# SLUG VALIDATION
# ============================================================

def is_valid_slug(slug: str) -> bool:
    """
    Validate slug format.
    
    Args:
        slug: Slug to validate
    
    Returns:
        True if slug is valid
    
    Examples:
        >>> is_valid_slug("hello-world")
        True
        
        >>> is_valid_slug("Hello World")
        False
        
        >>> is_valid_slug("hello_world")
        False
        
        >>> is_valid_slug("hello-world-123")
        True
    """
    if not slug or not isinstance(slug, str):
        return False
    
    # Must be lowercase alphanumeric with hyphens
    if not re.match(r'^[a-z0-9\-]+$', slug):
        return False
    
    # Cannot start or end with hyphen
    if slug.startswith('-') or slug.endswith('-'):
        return False
    
    # Cannot have consecutive hyphens
    if '--' in slug:
        return False
    
    # Max length
    if len(slug) > DEFAULT_MAX_LENGTH:
        return False
    
    # Min length (at least 1 character)
    if len(slug) < 1:
        return False
    
    return True


def normalize_slug(slug: str, max_length: int = DEFAULT_MAX_LENGTH) -> str:
    """
    Normalize a slug to ensure it's valid.
    
    Args:
        slug: Slug to normalize
        max_length: Maximum length
    
    Returns:
        Normalized slug
    
    Examples:
        >>> normalize_slug("Hello World!")
        "hello-world"
        
        >>> normalize_slug("--hello--world--")
        "hello-world"
    """
    if not slug:
        return DEFAULT_EMPTY_SLUG
    
    # Convert to lowercase
    slug = slug.lower()
    
    # Normalize unicode
    slug = normalize_text(slug)
    
    # Replace invalid characters with hyphens
    slug = re.sub(r'[^a-z0-9\-]', '-', slug)
    
    # Remove consecutive hyphens
    slug = re.sub(r'\-+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Truncate
    if len(slug) > max_length:
        slug = slug[:max_length]
        slug = re.sub(r'\-[^-]*$', '', slug)
    
    return slug or DEFAULT_EMPTY_SLUG


# ============================================================
# SLUG EXTRACTION
# ============================================================

def extract_slug_from_url(url: str) -> Optional[str]:
    """
    Extract slug from URL.
    
    Args:
        url: Full URL
    
    Returns:
        Extracted slug or None
    
    Examples:
        >>> extract_slug_from_url("https://example.com/courses/my-course")
        "my-course"
        
        >>> extract_slug_from_url("/courses/my-course")
        "my-course"
    """
    if not url:
        return None
    
    # Remove query parameters
    url = url.split('?')[0]
    
    # Get last part of URL
    slug = url.rstrip('/').split('/')[-1]
    
    return slug if slug else None


def is_slug_in_url(url: str, slug: str) -> bool:
    """
    Check if slug is present in URL.
    
    Args:
        url: URL to check
        slug: Slug to find
    
    Returns:
        True if slug is in URL
    """
    if not url or not slug:
        return False
    
    return slug in url


# ============================================================
# BULK SLUG GENERATION
# ============================================================

def generate_bulk_slugs(
    titles: List[str],
    existing_slugs: Optional[List[str]] = None,
    max_length: int = DEFAULT_MAX_LENGTH,
) -> List[str]:
    """
    Generate slugs for multiple titles.
    
    Args:
        titles: List of titles
        existing_slugs: List of existing slugs
        max_length: Maximum length
    
    Returns:
        List of unique slugs
    
    Examples:
        >>> generate_bulk_slugs(["Course 1", "Course 2"])
        ["course-1", "course-2"]
    """
    if existing_slugs is None:
        existing_slugs = []
    
    # Copy existing slugs to avoid modifying original
    used_slugs = existing_slugs.copy()
    generated_slugs = []
    
    for title in titles:
        slug = generate_slug_from_title(title, used_slugs, max_length)
        generated_slugs.append(slug)
        used_slugs.append(slug)
    
    return generated_slugs


# ============================================================
# SLUG COMPARISON
# ============================================================

def slugs_match(slug1: str, slug2: str) -> bool:
    """
    Check if two slugs match (case-insensitive).
    
    Args:
        slug1: First slug
        slug2: Second slug
    
    Returns:
        True if slugs match
    """
    if not slug1 or not slug2:
        return False
    
    return slug1.lower() == slug2.lower()


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Generation
    'generate_slug',
    'generate_unique_slug',
    'generate_slug_from_title',
    'generate_bulk_slugs',
    
    # Validation
    'is_valid_slug',
    'normalize_slug',
    
    # Extraction
    'extract_slug_from_url',
    'is_slug_in_url',
    
    # Comparison
    'slugs_match',
    
    # Utilities
    'normalize_text',
    'clean_text_for_slug',
]