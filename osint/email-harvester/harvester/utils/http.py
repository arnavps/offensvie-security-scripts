import httpx
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

from .logger import logger

class AsyncHttpClient:
    """
    A robust asynchronous HTTP client wrapper with built-in retry logic,
    timeout handling, and rotating user agents.
    """
    def __init__(self, timeout_seconds: int = 15):
        self.timeout = timeout_seconds
        # Common user agents to avoid trivial blocking
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/114.0"
        ]
        self._current_ua_index = 0

    def _get_next_user_agent(self) -> str:
        ua = self.user_agents[self._current_ua_index]
        self._current_ua_index = (self._current_ua_index + 1) % len(self.user_agents)
        return ua

    # Retry on specific network errors or timeouts. Max 3 attempts. Backoff exponentially (e.g., 2s, 4s).
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True
    )
    async def get(self, client: httpx.AsyncClient, url: str, params: dict = None) -> httpx.Response:
        """
        Performs an asynchronous GET request with retries.
        """
        headers = {
            "User-Agent": self._get_next_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5"
        }
        
        logger.debug(f"Requesting: {url} | Params: {params}")
        response = await client.get(url, params=params, headers=headers, timeout=self.timeout)
        
        # Raise HTTPStatusError for 4xx or 5xx responses so we can catch them if needed
        response.raise_for_status()
        return response
