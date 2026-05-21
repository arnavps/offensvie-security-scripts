"""
Domain and target validation utilities for the Subdomain Collector.
Protects the reconnaissance pipeline from out-of-scope targets and injection.
"""

import re
from typing import Optional

class DomainValidator:
    # RFC 1035 compliant regex for root domain validation
    # Matches strings like "google.com", "sub.target.co.uk"
    DOMAIN_REGEX = re.compile(
        r'^([a-zA-Z0-9](([a-zA-Z0-9-]){0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$'
    )
    
    # Safe validation for subdomain character structures
    SUBDOMAIN_CHARS = re.compile(r'^[a-zA-Z0-9.-]+$')

    @classmethod
    def is_valid_domain(cls, domain: str) -> bool:
        """
        Validates if the provided string is a syntactically correct root domain or subdomain.
        Ensures strings do not contain special characters, paths, or injection inputs.
        """
        if not domain or len(domain) > 253:
            return False
        return bool(cls.DOMAIN_REGEX.match(domain))

    @classmethod
    def is_in_scope(cls, hostname: str, root_domain: str) -> bool:
        """
        Checks if a discovered hostname is strictly within the scope of the target root domain.
        Prevents scope-leaks (e.g. "target.com.attacker.com" is out-of-scope for "target.com").
        """
        hostname = hostname.strip().lower()
        root_domain = root_domain.strip().lower()
        
        if not hostname or not root_domain:
            return False
            
        if hostname == root_domain:
            return True
            
        # Must end with ".root_domain" to be a valid subdomain of root_domain
        return hostname.endswith(f".{root_domain}")

    @classmethod
    def sanitize_discovered_name(cls, raw_name: str) -> Optional[str]:
        """
        Normalizes and sanitizes a raw subdomain parsed from passive tools.
        Removes common prefix wildcards like '*.' or leading/trailing whitespaces.
        Returns None if the result is invalid.
        """
        if not raw_name:
            return None
            
        cleaned = raw_name.strip().lower()
        
        # Remove common wildcards
        if cleaned.startswith("*."):
            cleaned = cleaned[2:]
        elif cleaned.startswith("*"):
            cleaned = cleaned[1:]
            
        # Clean any trailing dots
        cleaned = cleaned.rstrip('.')
        
        if not cls.SUBDOMAIN_CHARS.match(cleaned):
            return None
            
        return cleaned if cls.is_valid_domain(cleaned) else None
