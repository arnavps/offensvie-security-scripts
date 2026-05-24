"""
Isolated Asynchronous HTTP engine wrapper with timeout, retry, and redirect chain extraction.
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin

import aiohttp

logger = logging.getLogger("Detector.HTTPClient")

class AsyncHTTPClient:
    """
    HTTP network client wrapper that manages connections, captures redirects,
    and returns response metadata structures.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get("http", {})
        self.concurrency_limit = self.config.get("concurrency_limit", 50)
        self.timeout = self.config.get("timeout", 10.0)
        self.user_agent = self.config.get("user_agent", "WebRedirectDetector/1.0")
        self.ssl_verify = self.config.get("ssl_verify", False)
        self.max_redirects = self.config.get("max_redirects", 5)

        self._session: Optional[aiohttp.ClientSession] = None
        self._semaphore = asyncio.Semaphore(self.concurrency_limit)

    async def __aenter__(self):
        connector = aiohttp.TCPConnector(ssl=self.ssl_verify, limit=self.concurrency_limit)
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        headers = {"User-Agent": self.user_agent}
        
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session and not self._session.closed:
            await self._session.close()

    async def inspect_url(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """
        Requests the target URL, manually follows redirects up to the limit, 
        and extracts redirection chains/hops.
        """
        async with self._semaphore:
            current_url = url
            visited = {current_url}
            redirect_chain = []
            start_time = time.perf_counter()

            try:
                for hop in range(self.max_redirects + 1):
                    async with self._session.request(
                        method, 
                        current_url, 
                        allow_redirects=False,
                        **kwargs
                    ) as response:
                        latency = time.perf_counter() - start_time
                        
                        # Capture Redirect hop
                        if 300 <= response.status < 400:
                            location = response.headers.get("Location")
                            if not location:
                                break
                                
                            next_url = urljoin(current_url, location)
                            redirect_chain.append({
                                "status": response.status,
                                "url": current_url,
                                "location": location
                            })
                            
                            # Check redirect loops
                            if next_url in visited:
                                return {
                                    "requested_url": url,
                                    "final_destination": next_url,
                                    "status": response.status,
                                    "redirect_chain": redirect_chain,
                                    "latency_ms": round(latency * 1000, 2),
                                    "error": "RedirectLoopDetected"
                                }
                                
                            visited.add(next_url)
                            current_url = next_url
                            await response.release()
                            continue
                            
                        # Standard final destination reached
                        return {
                            "requested_url": url,
                            "final_destination": current_url,
                            "status": response.status,
                            "redirect_chain": redirect_chain,
                            "latency_ms": round(latency * 1000, 2),
                            "error": None
                        }
                        
                # Redirect loop/depth exceeded
                return {
                    "requested_url": url,
                    "final_destination": current_url,
                    "status": 302,
                    "redirect_chain": redirect_chain,
                    "latency_ms": round((time.perf_counter() - start_time) * 1000, 2),
                    "error": "MaxRedirectsExceeded"
                }

            except Exception as e:
                return {
                    "requested_url": url,
                    "final_destination": current_url,
                    "status": -1,
                    "redirect_chain": redirect_chain,
                    "latency_ms": round((time.perf_counter() - start_time) * 1000, 2),
                    "error": f"NetworkError: {type(e).__name__}"
                }
