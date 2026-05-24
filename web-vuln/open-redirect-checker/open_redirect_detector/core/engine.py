"""
Inspection and analysis orchestration engine.
Handles parallel task execution, registers modules, and maps findings.
"""
import asyncio
import logging
from typing import List, Dict, Any, Type

from open_redirect_detector.core.base_checker import BaseRedirectChecker
from open_redirect_detector.core.http_client import AsyncHTTPClient

logger = logging.getLogger("Detector.Engine")

class DetectionEngine:
    """
    Central orchestration engine managing dynamic checkers and connection pools.
    """
    def __init__(self, target_url: str, config: Dict[str, Any]):
        self.target_url = target_url
        self.config = config
        self.checkers: List[Type[BaseRedirectChecker]] = []

    def register_checker(self, checker_cls: Type[BaseRedirectChecker]):
        """
        Registers a modular checker class for scanning target execution.
        """
        self.checkers.append(checker_cls)
        logger.debug(f"Registered dynamic checker: {checker_cls.__name__}")

    async def execute(self) -> List[Dict[str, Any]]:
        """
        Launches registered checkers concurrently using a shared connections pool client.
        """
        if not self.checkers:
            logger.warning("No redirection checkers registered. Exiting execution engine.")
            return []

        logger.info(f"Launching scanning engine with {len(self.checkers)} vulnerability modules...")
        
        findings: List[Dict[str, Any]] = []
        
        async with AsyncHTTPClient(self.config) as client:
            # Instantiate checkers
            instances = [cls(self.target_url, self.config) for cls in self.checkers]
            tasks = [inst.run_checks(client) for inst in instances]
            
            # Concurrently process vulnerability checks
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for idx, res in enumerate(results):
                if isinstance(res, Exception):
                    logger.error(f"Checker '{self.checkers[idx].__name__}' crashed during run: {res}")
                    continue
                findings.extend(res)
                
        logger.info(f"Scanning completed. Captured {len(findings)} report items.")
        return findings
