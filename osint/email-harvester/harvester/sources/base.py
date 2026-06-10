from abc import ABC, abstractmethod
from typing import Set

import httpx

from ..core.models import EmailResult, TargetDomain
from ..utils.extractors import EmailExtractor
from ..utils.http import AsyncHttpClient
from ..utils.logger import logger


class BaseSource(ABC):
    """
    Abstract base class for all OSINT data sources.
    Forces all plugins to implement the `run` method.
    """
    def __init__(self, target: TargetDomain):
        self.target = target
        self.domain = target.domain
        self.extractor = EmailExtractor(self.domain)
        # Inheriting classes should set this
        self.name = "BaseSource" 

    @abstractmethod
    async def run(self, client: httpx.AsyncClient, http_client: AsyncHttpClient) -> Set[EmailResult]:
        """
        Executes the scraping logic for this specific source.
        Must be implemented by subclasses.
        
        :param client: The active httpx.AsyncClient session.
        :param http_client: Our custom robust HTTP client with retry logic.
        :return: A set of strictly validated EmailResult objects.
        """
        pass

    def _create_results(self, raw_emails: Set[str], source_url: str = None) -> Set[EmailResult]:
        """
        Helper method to convert raw string emails into validated Pydantic models.
        """
        results = set()
        for raw_email in raw_emails:
            try:
                # Validation happens inside the model
                result = EmailResult(
                    email=raw_email,
                    source=self.name,
                    url=source_url
                )
                results.add(result)
            except ValueError as e:
                logger.debug(f"[{self.name}] Failed to validate email '{raw_email}': {e}")
                
        return results
