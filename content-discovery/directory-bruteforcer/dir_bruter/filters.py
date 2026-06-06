"""
Filters Module
Implements logic to distinguish genuine responses from false positives (like Soft 404s).
"""
import httpx
from typing import Optional

class ResponseFilter:
    def __init__(self):
        self.baseline_signature: Optional[int] = None
        # Common valid status codes for content discovery
        self.valid_status_codes = {200, 204, 301, 302, 307, 401, 403, 500}

    def set_baseline(self, response: httpx.Response):
        """
        Sets the baseline signature based on a request to a known non-existent path.
        Currently uses response body length, but could be extended to use word counts or DOM hashes.
        """
        if response.status_code == 200:
            self.baseline_signature = len(response.content)

    def is_valid(self, response: httpx.Response) -> bool:
        """
        Determines if a response indicates a valid discovery.
        """
        # 1. Filter by status code
        if response.status_code not in self.valid_status_codes:
            return False

        # 2. Soft 404 check
        if response.status_code == 200 and self.baseline_signature is not None:
            # If the response length is exactly the same as our baseline "not found" page,
            # it's highly likely to be a soft 404.
            # In a production tool, we might use a threshold (e.g., within 5% of length) 
            # or a fuzzy hash to be more resilient to dynamic content (like timestamps on error pages).
            if len(response.content) == self.baseline_signature:
                return False

        return True
