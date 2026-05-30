import concurrent.futures
import threading
import logging
from typing import List, Dict, Any

from smb_enum.config import ScanConfig
from smb_enum.core.smb_client import SMBEnumClient
from smb_enum.utils.exceptions import (
    AuthenticationError,
    HostUnreachableError,
    ConnectionRefusedError
)

logger = logging.getLogger("smb_enum")

class Scanner:
    """
    Orchestrates the enumeration across multiple targets using a ThreadPoolExecutor.
    """
    
    def __init__(self, config: ScanConfig):
        self.config = config
        self.results: List[Dict[str, Any]] = []
        self._lock = threading.Lock() # Lock to protect the results list during concurrent appends
        
    def _scan_host(self, target: str) -> None:
        """
        Worker function executed by the thread pool for a single host.
        """
        client = SMBEnumClient(target, port=self.config.port, timeout=self.config.timeout)
        
        try:
            # 1. Connect and Authenticate
            logger.debug(f"[{target}] Attempting connection...")
            client.connect_and_login(
                username=self.config.username,
                password=self.config.password,
                domain=self.config.domain,
                hashes=self.config.hash
            )
            
            logger.info(f"[{target}] [bold green]Authentication Successful[/bold green] (Null Session: {self.config.is_null_session})", extra={"markup": True})
            
            # 2. Enumerate Shares
            shares = client.list_shares()
            if not shares:
                logger.info(f"[{target}] No shares found or access denied to RPC enumeration.")
                return
                
            logger.info(f"[{target}] Found {len(shares)} shares.")
            
            # 3. Check Access for each share
            for share in shares:
                share_name = share['name']
                remark = share['remark']
                
                # Filter out default administrative shares if we only want "real" data shares
                # (We keep them here, but flag them. A future feature could add a --exclude-default flag)
                
                logger.debug(f"[{target}] Checking access for share: {share_name}")
                read_access, write_access = client.check_access(share_name, check_write=self.config.check_write)
                
                result = {
                    "host": target,
                    "share": share_name,
                    "read": read_access,
                    "write": write_access,
                    "remark": remark
                }
                
                # Thread-safe append
                with self._lock:
                    self.results.append(result)
                    
                if read_access:
                    # Live notification of a juicy finding
                    logger.info(f"[{target}] [bold yellow]READ ACCESS[/bold yellow] confirmed on share: {share_name}", extra={"markup": True})
                    if write_access:
                        logger.info(f"[{target}] [bold red]WRITE ACCESS[/bold red] confirmed on share: {share_name}", extra={"markup": True})

        except HostUnreachableError as e:
            logger.debug(str(e)) # Too noisy to print as INFO during a big subnet scan
        except ConnectionRefusedError as e:
            logger.debug(str(e))
        except AuthenticationError as e:
            logger.warning(f"[bold red]Auth Error[/bold red] {e}", extra={"markup": True})
        except Exception as e:
            logger.error(f"[{target}] Unexpected error: {e}")
        finally:
            client.disconnect()

    def run(self, targets: List[str]) -> List[Dict[str, Any]]:
        """
        Executes the scan against a list of parsed IP addresses/hostnames.
        """
        logger.info(f"Starting scan against {len(targets)} targets with {self.config.threads} threads...")
        
        # We use a ThreadPool instead of ProcessPool because network I/O is the bottleneck,
        # and Threads are lighter to spin up and share memory (self.results) easily.
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.threads) as executor:
            # We map the targets to the worker function
            # list() forces the generator to evaluate, blocking until all are done
            list(executor.map(self._scan_host, targets))
            
        logger.info("Scan complete.")
        return self.results
