"""
Subdomain Collector: Asynchronous Engineering-Grade Reconnaissance Framework.
Main CLI Entry Point.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Dict, Any

import yaml

from subdomain_collector.core.engine import OrchestrationEngine
from subdomain_collector.modules.crtsh import CrtshCollector
from subdomain_collector.modules.hackertarget import HackerTargetCollector
from subdomain_collector.modules.brute_force import BruteForceCollector
from subdomain_collector.utils.logger import setup_logger
from subdomain_collector.utils.validator import DomainValidator

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Safely loads configurations from settings.yaml.
    Returns a blank config dictionary if not found.
    """
    if not os.path.exists(config_path):
        # Gracefully handle missing config files using safe empty dict structure
        return {}
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

async def run_pipeline(args: argparse.Namespace, config: Dict[str, Any], logger: logging.Logger):
    domain = args.domain.strip().lower()
    
    # 1. Validate domain syntax
    if not DomainValidator.is_valid_domain(domain):
        logger.error(f"Malformed or invalid domain name format: '{domain}'. Exiting.")
        sys.exit(1)

    logger.info(f"Target reconnaissance scope locked: {domain}")
    
    # 2. Initialize orchestrator
    engine = OrchestrationEngine(domain, config)
    
    # 3. Register collectors based on CLI mode
    mode = args.mode.lower()
    
    if mode in ("passive", "all"):
        engine.register_collector(CrtshCollector)
        engine.register_collector(HackerTargetCollector)
        
    if mode in ("active", "all"):
        engine.register_collector(BruteForceCollector)
        
    # 4. Execute pipeline
    logger.info(f"Executing pipeline in '{mode}' mode...")
    results = await engine.run()
    
    if not results:
        logger.warning("Pipeline finished. No active subdomains discovered.")
        return
        
    # Filter active hosts
    active_hosts = [host for host in results if host["status"] == "Active"]
    
    # Clean output print
    print("\n" + "=" * 60)
    print(f" RECONNAISSANCE REPORT FOR: {domain}")
    print("=" * 60)
    if active_hosts:
        for host in active_hosts:
            ips_str = ", ".join(host["ips"])
            print(f"[+] {host['subdomain']:<35} ->  [{ips_str}]")
    else:
        print("[!] No actively resolving subdomains found.")
    print("=" * 60)
    print(f"Total resolved active subdomains: {len(active_hosts)}\n")

    # 5. Output file export
    if args.output:
        try:
            # Ensure target parent folders exist
            out_dir = os.path.dirname(os.path.abspath(args.output))
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
                
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4)
            logger.info(f"Full JSON intelligence report saved to: {args.output}")
        except IOError as e:
            logger.error(f"Failed to generate JSON output file: {str(e)}")

def main():
    # Setup base folder pathways for relative discovery
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_config = os.path.join(root_dir, "config", "settings.yaml")
    
    parser = argparse.ArgumentParser(
        description="Subdomain Collector: High-Performance Asynchronous Offensive Reconnaissance Utility.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("-d", "--domain", required=True, help="Target root domain to collect subdomains for (e.g. target.com)")
    parser.add_argument("-o", "--output", help="Path to save JSON-formatted intelligence reports")
    parser.add_argument("-c", "--config", default=default_config, help="Path to settings.yaml configuration")
    parser.add_argument(
        "--mode", 
        choices=["passive", "active", "all"], 
        default="all", 
        help="Reconnaissance discovery mode (default: all)"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable highly detailed verbose logging output")

    args = parser.parse_args()
    
    # Configure logs levels
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger("CollectorCore", log_level)
    
    # Load configuration
    config = load_config(args.config)
    
    try:
        asyncio.run(run_pipeline(args, config, logger))
    except KeyboardInterrupt:
        logger.warning("Pipeline execution forcefully aborted by operator.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Unhandled pipeline crash: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
