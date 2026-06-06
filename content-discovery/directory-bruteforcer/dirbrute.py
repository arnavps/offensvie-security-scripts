#!/usr/bin/env python3
"""
DirBruter: A professional async directory brute-forcing utility.
Entry point script.
"""
import asyncio
import sys

from dir_bruter.cli import parse_args
from dir_bruter.engine import Engine
from dir_bruter.utils.logger import logger

def main():
    try:
        config = parse_args()
        engine = Engine(config)
        
        # Suppress Unverified HTTPS warnings globally for this tool
        import warnings
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")
        
        asyncio.run(engine.run())
        
    except KeyboardInterrupt:
        logger.warning("\n[!] Scan interrupted by user (Ctrl+C). Exiting gracefully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"[!] Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Workaround for ProactorEventLoop on Windows causing exceptions on exit
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    main()
