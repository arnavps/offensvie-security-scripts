"""
Orchestration Engine for loading, scheduling, and running subdomain collector modules.
Integrates validation filters and forwards clean outputs to the resolver phase.
"""

import asyncio
import logging
from typing import Set, List, Dict, Any, Type

from subdomain_collector.core.base_collector import BaseCollector
from subdomain_collector.core.resolver import AsyncDNSResolver
from subdomain_collector.utils.validator import DomainValidator

class OrchestrationEngine:
    """
    Core engine managing the concurrent lifecycle of collection modules and validation steps.
    """
    def __init__(self, domain: str, config: Dict[str, Any]):
        self.domain = domain.strip().lower()
        self.config = config
        self.logger = logging.getLogger("Engine")
        self.collector_classes: List[Type[BaseCollector]] = []

    def register_collector(self, collector_cls: Type[BaseCollector]):
        """
        Registers a collector class to be executed by the orchestrator.
        """
        self.collector_classes.append(collector_cls)
        self.logger.debug(f"Registered collector class: {collector_cls.__name__}")

    async def run(self) -> List[Dict[str, Any]]:
        """
        Executes all registered collectors concurrently, aggregates and sanitizes the output,
        and runs the DNS verification pipeline.
        
        Returns:
            A list of dictionary records containing subdomains, resolution statuses, and IPs.
        """
        if not self.collector_classes:
            self.logger.warning("No collector modules registered. Exiting engine run.")
            return []

        self.logger.info(f"Launching {len(self.collector_classes)} collection modules...")
        
        # Instantiate collectors and schedule execution
        instances = [cls(self.domain, self.config) for cls in self.collector_classes]
        tasks = [inst.collect() for inst in instances]
        
        # Execute concurrently
        results: List[Set[str]] = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process and clean parsed domains
        raw_candidates: Set[str] = set()
        for idx, res in enumerate(results):
            if isinstance(res, Exception):
                self.logger.error(
                    f"Collector {self.collector_classes[idx].__name__} failed: {str(res)}"
                )
                continue
            raw_candidates.update(res)

        self.logger.info(f"Aggregated {len(raw_candidates)} total raw domain strings.")

        # Sanitize and apply in-scope constraint validation
        sanitized_candidates: Set[str] = set()
        for candidate in raw_candidates:
            clean_name = DomainValidator.sanitize_discovered_name(candidate)
            if clean_name and DomainValidator.is_in_scope(clean_name, self.domain):
                sanitized_candidates.add(clean_name)
            else:
                self.logger.debug(f"Filtered out-of-scope or invalid entry: '{candidate}'")

        self.logger.info(f"Refined to {len(sanitized_candidates)} unique, in-scope candidates.")

        if not sanitized_candidates:
            self.logger.warning("No valid subdomains discovered in collection phase.")
            return []

        # Forward validated set to DNS verification layer
        dns_validator = AsyncDNSResolver(self.config)
        verified_results = await dns_validator.verify_subdomains(sanitized_candidates, self.domain)
        
        return verified_results
