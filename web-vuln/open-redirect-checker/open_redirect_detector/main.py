"""
Open Redirect Detector: Main CLI entrypoint.
"""
import argparse
import asyncio
import logging
import os
import sys
from typing import Dict, Any

import yaml

# Dynamic parent path resolution to guarantee out-of-the-box execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from open_redirect_detector.core.engine import DetectionEngine
from open_redirect_detector.core.validator import DomainValidator
from open_redirect_detector.modules.param_mutation import ParamMutationChecker
from open_redirect_detector.modules.path_injection import PathInjectionChecker
from open_redirect_detector.utils.logger import setup_logger
from open_redirect_detector.utils.reporter import Exporter

def load_config(config_path: str) -> Dict[str, Any]:
    """
    Loads configurations from settings.yaml.
    """
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}

async def run_pipeline(args: argparse.Namespace, config: Dict[str, Any], logger: logging.Logger):
    target = args.target.strip()
    
    # 1. Normalize and validate input URL structure
    normalized_target = DomainValidator.normalize_target(target)
    if not normalized_target or not DomainValidator.is_valid_url(normalized_target):
        logger.error(f"Malformed or invalid target URL format: '{target}'. Exiting.")
        sys.exit(1)

    logger.info(f"Target reconnaissance lock acquired: {normalized_target}")

    # 2. Initialize orchestrator engine
    engine = DetectionEngine(normalized_target, config)
    
    # 3. Register collectors / checking modules
    engine.register_checker(ParamMutationChecker)
    engine.register_checker(PathInjectionChecker)
    
    # 4. Execute checks
    logger.info("Executing open redirect security inspection pipeline...")
    findings = await engine.execute()
    
    # Print clean report to console
    print("\n" + "=" * 60)
    print(f" SECURITY DETECTION REPORT FOR: {normalized_target}")
    print("=" * 60)
    
    vulnerable_findings = [f for f in findings if f.get("is_vulnerable")]
    
    if vulnerable_findings:
        print("[!] WARNING: TARGET IS VULNERABLE TO OPEN REDIRECTS!")
        print("-" * 60)
        for idx, item in enumerate(vulnerable_findings, 1):
            print(f"  [{idx}] Vector  : {item['vector']}")
            print(f"      Module  : {item['module']}")
            print(f"      Payload : {item['payload']}")
            print(f"      Fuzzed  : {item['test_url']}")
            print(f"      Resolved: {item['resolved_url']}")
            print(f"      Status  : {item['status_code']}")
            print("-" * 60)
    else:
        print("[+] Congratulations! No open redirect vulnerabilities detected.")
        
    print(f"Total vector paths tested: {len(findings)}")
    print(f"Total vulnerabilities confirmed: {len(vulnerable_findings)}")
    print("=" * 60 + "\n")

    # 5. Export JSON report
    if args.output:
        if Exporter.export_json(findings, args.output):
            logger.info(f"Full JSON vulnerability report saved to: {args.output}")
        else:
            logger.error(f"Failed to generate JSON output report file: '{args.output}'")

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_config = os.path.join(root_dir, "config", "settings.yaml")

    parser = argparse.ArgumentParser(
        description="Open Redirect Detector: High-Performance Modular Security Analysis Framework.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("-t", "--target", required=True, help="Target URL domain or address to inspect (e.g. target.com/login)")
    parser.add_argument("-o", "--output", help="Path to save JSON-formatted intelligence reports")
    parser.add_argument("-c", "--config", default=default_config, help="Path to settings.yaml configuration")
    parser.add_argument("--verbose", action="store_true", help="Enable highly detailed verbose logging output")

    args = parser.parse_args()
    
    # Configure logs levels
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logger("DetectorCore", log_level)
    
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
