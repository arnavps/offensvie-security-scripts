"""
Passive Subdomain Collector module using HackerTarget Host Search API.
Queries public data indexes containing DNS records for target domains.
"""

import httpx
from typing import Set
from subdomain_collector.core.base_collector import BaseCollector

class HackerTargetCollector(BaseCollector):
    """
    Queries HackerTarget hostsearch endpoint.
    """
    async def collect(self) -> Set[str]:
        subdomains: Set[str] = set()
        url = f"https://api.hackertarget.com/hostsearch/?q={self.domain}"
        
        headers = {
            "User-Agent": self.user_agent
        }
        
        self.logger.info(f"Querying HackerTarget host search indexes for: {self.domain}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    lines = response.text.strip().split("\n")
                    for line in lines:
                        if not line or "," not in line:
                            continue
                        # HackerTarget returns comma-separated fields: hostname,ip_address
                        hostname = line.split(",")[0].strip().lower()
                        if hostname:
                            subdomains.add(hostname)
                else:
                    self.logger.warning(
                        f"HackerTarget API returned non-200 status code: {response.status_code}"
                    )
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP request failed: {str(e)}")
        except Exception as e:
            self.logger.error(
                f"Error parsing HackerTarget records: {type(e).__name__} - {str(e)}"
            )
            
        self.logger.info(f"Retrieved {len(subdomains)} candidates from HackerTarget")
        return subdomains
