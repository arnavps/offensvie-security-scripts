"""
Abstract Base Class for all open redirect vulnerability scanning modules.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

from open_redirect_detector.core.http_client import AsyncHTTPClient

class BaseRedirectChecker(ABC):
    """
    Subclass interface that all vulnerability checkers must implement.
    Allows modular loading and polymorphic execution.
    """
    def __init__(self, target_url: str, config: Dict[str, Any]):
        self.target_url = target_url
        self.config = config
        self.payload_config = config.get("payloads", {})

    @abstractmethod
    async def run_checks(self, client: AsyncHTTPClient) -> List[Dict[str, Any]]:
        """
        Executes checker inspection asynchronously.
        
        Args:
            client: The shared AsyncHTTPClient session wrapper.
            
        Returns:
            A list of validation/finding result dictionaries.
        """
        pass
