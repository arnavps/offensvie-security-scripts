import re
from typing import List, Set


class EmailExtractor:
    """
    Handles regex-based extraction of emails from raw text/HTML.
    """
    def __init__(self, domain: str):
        self.domain = domain
        # Strict regex: matches anything looking like an email ending in the exact domain
        # We use a raw string and compile it for performance.
        # This regex tries to avoid catching false positives like 'image.png@example.com'
        pattern = r'[a-zA-Z0-9._%+-]+@(?:[a-zA-Z0-9-]+\.)*' + re.escape(domain)
        self.regex = re.compile(pattern, re.IGNORECASE)

    def extract(self, text: str) -> Set[str]:
        """
        Extracts all emails matching the domain from the provided text.
        Returns a set to immediately deduplicate raw strings.
        """
        if not text:
            return set()
            
        # Clean common HTML obfuscation before running the regex
        # e.g., 'user [at] example.com' -> 'user@example.com'
        text = text.replace("[at]", "@").replace("(at)", "@").replace(" [at] ", "@").replace(" (at) ", "@")
        
        matches = self.regex.findall(text)
        
        valid_emails = set()
        # Bad extensions that usually indicate a false positive from a filename
        bad_extensions = [".png", ".jpg", ".jpeg", ".gif", ".css", ".js", ".svg", ".webp"]

        for match in matches:
            clean_email = match.lower().strip()
            
            # Simple heuristic: Reject if the local part (before @) ends with a common file extension
            local_part = clean_email.split('@')[0]
            if any(local_part.endswith(ext) for ext in bad_extensions):
                continue
                
            valid_emails.add(clean_email)
            
        return valid_emails
