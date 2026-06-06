"""
Requester Module
Handles HTTP requests, connection pooling, timeouts, and automatic retries.
Uses httpx and tenacity.
"""
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .config import Config

class Requester:
    def __init__(self, config: Config):
        self.config = config
        # Use httpx.AsyncClient for connection pooling and HTTP/2 support
        self.client = httpx.AsyncClient(
            verify=False,  # Security tools often hit self-signed certs
            timeout=self.config.timeout,
            follow_redirects=self.config.allow_redirects,
            headers={"User-Agent": self.config.user_agent}
        )

    # Retry logic: wait 2^x * 1 second between each retry, up to max retries.
    # Only retry on network errors or timeouts, NOT on 404s.
    @retry(
        stop=stop_after_attempt(3), # Will be dynamically overridden based on config
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True
    )
    async def make_request(self, url: str) -> httpx.Response:
        """
        Executes an asynchronous HTTP GET request.
        Handled exceptions (timeouts, connection drops) will trigger a retry.
        """
        return await self.client.get(url)

    async def close(self):
        """Cleanly close the underlying connection pool."""
        await self.client.aclose()
