"""
Asynchronous DNS Validation Engine for Subdomain Collector.
Features custom resolver pool configuration, concurrency limiting, and pre-flight wildcard checks.
"""

import asyncio
import logging
import random
import string
from typing import Set, Dict, List, Any
import dns.asyncresolver
import dns.exception

class AsyncDNSResolver:
    """
    High-performance thread-safe asynchronous resolver.
    """
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger("Resolver")
        self.dns_config = config.get("dns", {})
        
        # Load resolvers, concurrency limit, and timeouts
        self.nameservers = self.dns_config.get("resolvers", ["1.1.1.1", "8.8.8.8"])
        self.concurrency_limit = self.dns_config.get("concurrency_limit", 100)
        self.timeout = self.dns_config.get("timeout", 4.0)
        
        # Initialize native async dns resolver
        self.resolver = dns.asyncresolver.Resolver()
        self.resolver.nameservers = self.nameservers
        self.resolver.timeout = self.timeout
        self.resolver.lifetime = self.timeout
        
        # Concurrency throttle
        self.semaphore = asyncio.Semaphore(self.concurrency_limit)
        
        # Wildcard status
        self.wildcard_detected = False
        self.wildcard_ips: Set[str] = set()

    async def detect_wildcard(self, root_domain: str) -> bool:
        """
        Executes a pre-flight check to detect wildcard DNS resolution.
        Queries a highly randomized subdomain. If it resolves, wildcard is active.
        """
        random_prefix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
        test_subdomain = f"{random_prefix}.{root_domain}"
        
        self.logger.info(f"Running wildcard DNS pre-flight check on: {test_subdomain}")
        try:
            answers = await self.resolver.resolve(test_subdomain, 'A')
            self.wildcard_ips = {ans.to_text() for ans in answers}
            self.wildcard_detected = True
            self.logger.warning(
                f"Wildcard DNS resolution detected! Random subdomain resolved to: {', '.join(self.wildcard_ips)}"
            )
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            self.logger.info("No wildcard DNS resolution active. Clean validation environment.")
            self.wildcard_detected = False
            return False
        except Exception as e:
            self.logger.warning(f"Could not complete wildcard pre-flight check: {type(e).__name__}")
            return False

    async def _resolve_single(self, subdomain: str) -> Dict[str, Any]:
        """
        Resolves a single subdomain A record asynchronously with concurrency control.
        """
        async with self.semaphore:
            try:
                answers = await self.resolver.resolve(subdomain, 'A')
                ips = {ans.to_text() for ans in answers}
                
                # Filter wildcard matches if wildcard is active
                if self.wildcard_detected and ips.issubset(self.wildcard_ips):
                    return {
                        "subdomain": subdomain,
                        "status": "WildcardPolluted",
                        "ips": list(ips)
                    }
                    
                return {
                    "subdomain": subdomain,
                    "status": "Active",
                    "ips": list(ips)
                }
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
                return {"subdomain": subdomain, "status": "Inactive", "ips": []}
            except dns.exception.Timeout:
                return {"subdomain": subdomain, "status": "Timeout", "ips": []}
            except Exception as e:
                return {"subdomain": subdomain, "status": f"Error: {type(e).__name__}", "ips": []}

    async def verify_subdomains(self, subdomains: Set[str], root_domain: str) -> List[Dict[str, Any]]:
        """
        Validates all subdomains in parallel, managing concurrency throttles.
        
        Args:
            subdomains: The set of unique subdomain hostnames to resolve.
            root_domain: Target domain for wildcard comparative filtering.
        """
        # Run wildcard check first
        await self.detect_wildcard(root_domain)
        
        self.logger.info(f"Initiating DNS validation for {len(subdomains)} candidates...")
        
        tasks = [self._resolve_single(sub) for sub in subdomains]
        results = await asyncio.gather(*tasks)
        
        # Log summary statistics
        active = sum(1 for r in results if r["status"] == "Active")
        polluted = sum(1 for r in results if r["status"] == "WildcardPolluted")
        
        self.logger.info(f"Resolution complete: {active} Active, {polluted} Filtered Wildcards.")
        return results
