import html
import re

def sanitize_text(text: str) -> str:
    """
    Sanitize text input by removing unsafe HTML/script tags and trimming whitespace.
    Protects against XSS and template injection attacks.
    """
    if not text:
        return ""
    # Strip script and style blocks
    cleaned = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r'<style.*?>.*?</style>', '', cleaned, flags=re.IGNORECASE | re.DOTALL)
    # Strip raw HTML tags
    cleaned = re.sub(r'<[^>]*>', '', cleaned)
    # Unescape any legitimate entities then escape
    cleaned = html.escape(cleaned.strip())
    # Return normalized text
    return html.unescape(cleaned).strip()

def sanitize_filename(filename: str) -> str:
    """
    Sanitize uploaded filenames to prevent directory traversal attacks (e.g., ../ or \\).
    """
    import os
    base = os.path.basename(filename)
    clean = re.sub(r'[^a-zA-Z0-9_.-]', '_', base)
    return clean[:100]
