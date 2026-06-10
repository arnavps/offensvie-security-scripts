import asyncio
import urllib.parse
from typing import Set

import httpx
from bs4 import BeautifulSoup

from .base import BaseSource
from ..core.models import EmailResult, TargetDomain
from ..utils.http import AsyncHttpClient
from ..utils.logger import logger


class DuckDuckGoSearch(BaseSource):
    """
    Scrapes DuckDuckGo HTML results for emails.
    """
    def __init__(self, target: TargetDomain):
        super().__init__(target)
        self.name = "DuckDuckGo"
        # We search specifically for the "@domain.com" string in text
        self.base_url = "https://html.duckduckgo.com/html/"
        self.max_pages = 3 # Keep it small to avoid aggressive IP bans

    async def run(self, client: httpx.AsyncClient, http_client: AsyncHttpClient) -> Set[EmailResult]:
        results: Set[EmailResult] = set()
        
        # OSINT Dork: exact match for the email domain suffix
        query = f'"{self.domain}"'
        
        # DDG uses a POST mechanism for pagination, but the first page can be GET
        # We'll just do a simple scrape of the first few pages using the form action if needed,
        # but for simplicity in this example, we'll hit the first page.
        
        params = {"q": query}
        
        try:
            logger.info(f"[{self.name}] Searching for: {query}")
            response = await http_client.get(client, self.base_url, params=params)
            
            # Extract raw emails using the base class regex
            raw_emails = self.extractor.extract(response.text)
            
            # Convert to strictly typed Pydantic models
            new_results = self._create_results(raw_emails, source_url=str(response.url))
            results.update(new_results)
            
            logger.debug(f"[{self.name}] Found {len(new_results)} emails on page 1")
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"[{self.name}] Rate limited (429). Skipping further pages.")
            else:
                logger.error(f"[{self.name}] HTTP Error: {e}")
        except Exception as e:
            logger.error(f"[{self.name}] Unexpected error: {e}")
            
        return results

# You can easily add Bing, Google (harder without API), Yahoo, etc. by following this pattern.
