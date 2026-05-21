"""
Base class definition for all collection modules in the Subdomain Collector.
Provides common configuration interfaces, logging initialization, and execution templates.
"""

from abc import ABC, abstractmethod
from typing import Set, Dict, Any
import logging

class BaseCollector(ABC):
    """
    Abstract Base Class that must be implemented by any passive or active subdomain collector.
    Guarantees standard configuration structures and method signatures.
    """
    def __init__(self, domain: str, config: Dict[str, Any]):
        """
        Initializes the collector module.
        
        Args:
            domain: The root target domain (e.g., example.com)
            config: A dictionary representing tool settings and credentials loaded from settings.yaml
        """
        self.domain = domain.strip().lower()
        self.config = config
        
        # Access http/brute settings with safe defaults
        self.http_config = config.get("http", {})
        self.timeout = self.http_config.get("timeout", 10.0)
        self.user_agent = self.http_config.get("user_agent", "SubdomainCollector/1.0")
        
        # Configure logging dynamically under the subclass' namespace
        self.logger = logging.getLogger(f"Collector.{self.__class__.__name__}")

    @abstractmethod
    async def collect(self) -> Set[str]:
        """
        Abstract method to execute subdomain gathering.
        Must be implemented as an asynchronous method returning a set of discovered subdomains.
        
        Returns:
            A set of unique subdomain string records.
        """
        pass
