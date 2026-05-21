"""
Passive Subdomain Collector module using crt.sh Certificate Transparency logs.
Queries database records matching domain certificates via HTTPS.
"""

import httpx
from typing import Set
from subdomain_collector.core.base_collector import BaseCollector

class CrtshCollector(BaseCollector):
    """
    Scrapes Certificate Transparency logs passively from crt.sh.
    """
    async def collect(self) -> Set[str]:
        subdomains: Set[str] = set()
        
        # Output json format query for exact matches matching domain certificates
        url = f"https://crt.sh/?q=%.{self.domain}&output=json"
        
        headers = {
            "User-Agent": self.user_agent
        }
        
        self.logger.info(f"Querying Certificate Transparency logs on: {self.domain}")
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    for record in data:
                        name_value = record.get("name_value", "")
                        # crt.sh can group multiple hostnames separated by newlines
                        names = name_value.split("\n")
                        for name in names:
                            name = name.strip().lower()
                            if name:
                                subdomains.add(name)
                else:
                    self.logger.warning(
                        f"crt.sh returned non-200 status code: {response.status_code}"
                    )
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP request failed: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error parsing crt.sh logs: {type(e).__name__} - {str(e)}")
            
        self.logger.info(f"Retrieved {len(subdomains)} candidates from crt.sh")
        return subdomains
