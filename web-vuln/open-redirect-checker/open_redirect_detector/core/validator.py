"""
Target URL validator and normalizer.
"""
import re
from typing import Optional
from urllib.parse import urlparse, urlunparse

class DomainValidator:
    """
    Standardizes input targets before starting HTTP checks.
    """
    SCHEME_PATTERN = re.compile(r'^(https?|ftp)://', re.IGNORECASE)

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Validates if target URL structure has schema and authority components.
        """
        if not url:
            return False
        try:
            parsed = urlparse(url)
            return parsed.scheme.lower() in ("http", "https") and bool(parsed.netloc)
        except Exception:
            return False

    @classmethod
    def normalize_target(cls, url: str) -> Optional[str]:
        """
        Ensures a scheme prefix exists and structures the URL format cleanly.
        """
        if not url:
            return None
            
        clean_url = url.strip()
        if not cls.SCHEME_PATTERN.match(clean_url):
            clean_url = "https://" + clean_url
            
        try:
            parsed = urlparse(clean_url)
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            path = parsed.path if parsed.path else "/"
            
            return urlunparse((
                scheme,
                netloc,
                path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
        except Exception:
            return None
