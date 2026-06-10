import asyncio
import importlib
import inspect
import os
import pkgutil
from typing import Dict, List, Set, Type

import httpx

from .models import EmailResult, TargetDomain
from ..sources.base import BaseSource
from ..utils.http import AsyncHttpClient
from ..utils.logger import logger


class HarvesterEngine:
    """
    The core orchestrator. Dynamically loads modules, manages the async event loop,
    and handles global deduplication.
    """
    def __init__(self, target_domain: str, timeout: int = 15):
        # Validate domain via Pydantic model immediately
        self.target = TargetDomain(domain=target_domain)
        
        self.http_client = AsyncHttpClient(timeout_seconds=timeout)
        self.sources: List[BaseSource] = []
        
        # State management (thread/async safe by nature of asyncio single-threaded event loop)
        self.discovered_emails: Set[EmailResult] = set()

    def _discover_sources(self):
        """
        Dynamically imports all modules in the `sources` package and instantiates
        classes that inherit from BaseSource. This allows drop-in plugins.
        """
        import harvester.sources
        
        package = harvester.sources
        prefix = package.__name__ + "."
        
        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__, prefix):
            if ispkg:
                continue
            
            try:
                module = importlib.import_module(modname)
                # Inspect the module for classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Find classes that inherit from BaseSource (but are not BaseSource itself)
                    if issubclass(obj, BaseSource) and obj is not BaseSource:
                        # Instantiate the plugin with the target domain
                        plugin_instance = obj(target=self.target)
                        self.sources.append(plugin_instance)
                        logger.debug(f"Loaded source plugin: {plugin_instance.name}")
            except Exception as e:
                logger.error(f"Failed to load module {modname}: {e}")

    async def _run_source(self, source: BaseSource, client: httpx.AsyncClient):
        """Wrapper to run a single source and handle fatal plugin crashes safely."""
        try:
            logger.info(f"Starting module: {source.name}")
            results = await source.run(client, self.http_client)
            
            if results:
                logger.info(f"[green][+] {source.name} found {len(results)} emails[/green]")
                # Merge into the global set. Because EmailResult is frozen/hashable,
                # duplicates based on email string are automatically dropped by Python `set`.
                self.discovered_emails.update(results)
            else:
                logger.info(f"[-] {source.name} found 0 emails")
                
        except Exception as e:
            logger.error(f"[red][!] Fatal error in module {source.name}: {e}[/red]")

    async def execute(self) -> List[EmailResult]:
        """
        Main execution flow.
        1. Discover plugins.
        2. Create async HTTP session.
        3. Spin up concurrent tasks using asyncio.gather.
        """
        logger.info(f"Targeting Domain: [cyan]{self.target.domain}[/cyan]")
        
        self._discover_sources()
        if not self.sources:
            logger.error("No source plugins loaded. Exiting.")
            return []

        logger.info(f"Loaded {len(self.sources)} modules. Starting asynchronous harvesting...")

        # Use an async context manager to ensure the HTTP session is properly closed
        # even if the program crashes or is interrupted by the user (Ctrl+C).
        async with httpx.AsyncClient() as client:
            # Create a list of coroutines
            tasks = [self._run_source(source, client) for source in self.sources]
            
            # Execute them concurrently. return_exceptions=True means if one module crashes
            # entirely, it won't kill the other modules.
            await asyncio.gather(*tasks, return_exceptions=True)
            
        logger.info("Harvesting complete.")
        logger.info(f"Total Unique Emails Found: [green]{len(self.discovered_emails)}[/green]")
        
        # Sort results alphabetically by email for clean output
        return sorted(list(self.discovered_emails), key=lambda x: x.email)
