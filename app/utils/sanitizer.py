# ============================================================
# AETHER LINK - SANITIZER
# ============================================================

import re
import html
from typing import Optional, List

# Allow these HTML tags for rich text (safe for display)
ALLOWED_HTML_TAGS = ['b', 'i', 'u', 'strong', 'em', 'p', 'br', 'ul', 'ol', 'li']

# Maximum lengths for different fields
MAX_TEXT_LENGTH = 5000
MAX_BIO_LENGTH = 1000
MAX_TITLE_LENGTH = 255
MAX_USERNAME_LENGTH = 50
MAX_EMAIL_LENGTH = 255


def sanitize_html(text: str, allowed_tags: Optional[List[str]] = None) -> str:
    """
    Sanitize HTML to prevent XSS attacks.
    
    Args:
        text: Raw HTML text
        allowed_tags: List of allowed HTML tags
    
    Returns:
        Sanitized HTML text
    
    Examples:
        >>> sanitize_html("<script>alert('xss')</script>")
        "alert('xss')"
        
        >>> sanitize_html("<b>Hello</b> <script>alert('xss')</script>")
        "<b>Hello</b> alert('xss')"
    """
    if text is None:
        return ""
    
    # First, escape all HTML
    text = html.escape(text)
    
    # If no tags allowed, return escaped text
    if not allowed_tags:
        return text
    
    # Convert escaped tags back to HTML for allowed tags only
    for tag in allowed_tags:
        # Opening tag
        escaped_open = f'&lt;{tag}&gt;'
        if escaped_open in text:
            text = text.replace(escaped_open, f'<{tag}>')
        
        # Closing tag
        escaped_close = f'&lt;/{tag}&gt;'
        if escaped_close in text:
            text = text.replace(escaped_close, f'</{tag}>')
    
    # Remove any remaining unclosed tags (for safety)
    # Pattern: < followed by anything except >, followed by >
    text = re.sub(r'<[^>]*>', '', text)
    
    # Remove onclick, onerror, onload, etc. (event handlers)
    text = re.sub(r'on\w+="[^"]*"', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+=\'[^\']*\'', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+=[^\s>]*', '', text, flags=re.IGNORECASE)
    
    # Remove javascript: protocol
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    
    return text


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize plain text (remove dangerous characters).
    
    Args:
        text: Raw text
        max_length: Maximum length (default: MAX_TEXT_LENGTH)
    
    Returns:
        Sanitized text
    
    Examples:
        >>> sanitize_text("Hello\x00World")
        "HelloWorld"
        
        >>> sanitize_text("  Hello  ", 10)
        "Hello"
    """
    if text is None:
        return ""
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Remove control characters (except newline and tab)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Trim whitespace
    text = text.strip()
    
    # Truncate if needed
    if max_length is None:
        max_length = MAX_TEXT_LENGTH
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def sanitize_bio(text: str) -> str:
    """
    Sanitize user bio with HTML support.
    
    Args:
        text: Raw bio text
    
    Returns:
        Sanitized bio with allowed HTML
    """
    if text is None:
        return ""
    
    # First sanitize text
    text = sanitize_text(text, MAX_BIO_LENGTH)
    
    # Then allow basic HTML formatting
    text = sanitize_html(text, ALLOWED_HTML_TAGS)
    
    return text


def sanitize_title(text: str) -> str:
    """
    Sanitize title (no HTML).
    
    Args:
        text: Raw title text
    
    Returns:
        Sanitized title
    """
    if text is None:
        return ""
    
    # No HTML allowed in titles
    text = sanitize_text(text, MAX_TITLE_LENGTH)
    text = sanitize_html(text, [])
    
    return text


def sanitize_email(email: str) -> str:
    """
    Sanitize email address.
    
    Args:
        email: Raw email
    
    Returns:
        Sanitized email
    
    Examples:
        >>> sanitize_email(" Test@Example.com ")
        "test@example.com"
        
        >>> sanitize_email("test@example.com<script>")
        "test@example.com"
    """
    if email is None:
        return ""
    
    # Remove whitespace
    email = email.strip()
    
    # Convert to lowercase
    email = email.lower()
    
    # Remove dangerous characters (keep only valid email chars)
    email = re.sub(r'[^a-z0-9@._+-]', '', email)
    
    # Truncate
    if len(email) > MAX_EMAIL_LENGTH:
        email = email[:MAX_EMAIL_LENGTH]
    
    return email


def sanitize_username(username: str) -> str:
    """
    Sanitize username (alphanumeric + underscore only).
    
    Args:
        username: Raw username
    
    Returns:
        Sanitized username
    
    Examples:
        >>> sanitize_username(" Hello_World!@# ")
        "helloworld"
        
        >>> sanitize_username("User_123")
        "user_123"
    """
    if username is None:
        return ""
    
    # Remove whitespace
    username = username.strip()
    
    # Remove special characters (keep only alphanumeric and underscore)
    username = re.sub(r'[^a-zA-Z0-9_]', '', username)
    
    # Convert to lowercase
    username = username.lower()
    
    # Truncate
    if len(username) > MAX_USERNAME_LENGTH:
        username = username[:MAX_USERNAME_LENGTH]
    
    return username


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Raw filename
    
    Returns:
        Sanitized filename
    
    Examples:
        >>> sanitize_filename("../../../etc/passwd")
        "etc_passwd"
        
        >>> sanitize_filename("file<script>.pdf")
        "file_script_.pdf"
    """
    if filename is None:
        return ""
    
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove dangerous characters
    filename = re.sub(r'[^a-zA-Z0-9._\-]', '_', filename)
    
    # Remove consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Remove leading/trailing dots and underscores
    filename = filename.strip('._')
    
    # Truncate
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        if ext:
            name = name[:255 - len(ext) - 1]
            filename = f"{name}.{ext}"
        else:
            filename = filename[:255]
    
    return filename


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query.
    
    Args:
        query: Raw search query
    
    Returns:
        Sanitized search query
    """
    if query is None:
        return ""
    
    # Remove special characters
    query = re.sub(r'[^\w\s\-]', '', query)
    
    # Trim whitespace
    query = query.strip()
    
    # Truncate
    if len(query) > 100:
        query = query[:100]
    
    return query