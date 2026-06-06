"""
Engine Module
Core asynchronous orchestration. Manages the work queue and worker pool.
"""
import asyncio
import os
import httpx
from urllib.parse import urljoin
import json

from .config import Config
from .requester import Requester
from .filters import ResponseFilter
from .utils.logger import logger
from .utils.formatter import format_hit

class Engine:
    def __init__(self, config: Config):
        self.config = config
        self.requester = Requester(config)
        self.filter = ResponseFilter()
        # Bounded queue prevents loading massive wordlists entirely into memory
        self.queue = asyncio.Queue(maxsize=10000)
        self.results = []
        
    async def _producer(self):
        """Reads wordlist line-by-line and feeds the queue."""
        if not os.path.exists(self.config.wordlist_path):
            logger.error(f"Wordlist not found: {self.config.wordlist_path}")
            return

        try:
            with open(self.config.wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    word = line.strip()
                    if not word or word.startswith('#'):
                        continue
                        
                    # Queue base word
                    await self.queue.put(word)
                    
                    # Queue extended words if specified
                    for ext in self.config.extensions:
                        await self.queue.put(f"{word}{ext}")
                        
        except Exception as e:
            logger.error(f"Error reading wordlist: {e}")
            
    async def _worker(self):
        """Pulls words from the queue and executes HTTP requests."""
        while True:
            try:
                # Wait for an item, timeout allows workers to shut down gracefully
                word = await asyncio.wait_for(self.queue.get(), timeout=2.0)
            except asyncio.TimeoutError:
                # Queue is empty and no new items arrived within timeout
                break

            target_url = urljoin(str(self.config.target_url), word)
            
            try:
                response = await self.requester.make_request(target_url)
                
                if self.filter.is_valid(response):
                    format_hit(target_url, response)
                    self.results.append({
                        "url": target_url,
                        "status": response.status_code,
                        "size": len(response.content)
                    })
            except Exception as e:
                # Log debug info, but don't crash the worker
                logger.debug(f"Failed {target_url}: {str(e)}")
            finally:
                self.queue.task_done()

    async def _establish_baseline(self):
        """Fetch a non-existent path to establish a Soft 404 signature."""
        dummy_path = "this-path-definitely-does-not-exist-12345"
        url = urljoin(str(self.config.target_url), dummy_path)
        logger.info(f"Establishing baseline for Soft 404s using: {url}")
        try:
            response = await self.requester.make_request(url)
            self.filter.set_baseline(response)
            if self.filter.baseline_signature is not None:
                logger.info(f"Baseline established. Soft 404 size: {self.filter.baseline_signature} bytes")
        except Exception as e:
            logger.warning(f"Failed to establish baseline: {e}")

    def _save_results(self):
        """Save results to output file if configured."""
        if not self.config.output_file or not self.results:
            return
            
        try:
            with open(self.config.output_file, 'w') as f:
                json.dump(self.results, f, indent=4)
            logger.info(f"Results saved to {self.config.output_file}")
        except Exception as e:
            logger.error(f"Failed to save results: {e}")

    async def run(self):
        """Main execution orchestrator."""
        logger.info(f"Starting directory brute force against: {self.config.target_url}")
        logger.info(f"Threads: {self.config.threads} | Wordlist: {self.config.wordlist_path}")
        
        await self._establish_baseline()

        # Start producer task
        producer_task = asyncio.create_task(self._producer())
        
        # Start worker tasks
        workers = [asyncio.create_task(self._worker()) for _ in range(self.config.threads)]
        
        # Wait for producer to finish populating queue
        await producer_task
        
        # Wait for queue to be fully processed by workers
        await self.queue.join()
        
        # Cancel workers if any are hung
        for w in workers:
            w.cancel()
            
        await self.requester.close()
        self._save_results()
        logger.info("Scan complete.")
