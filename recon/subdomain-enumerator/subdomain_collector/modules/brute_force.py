"""
Active Subdomain Candidate Generator using local wordlists.
Reads prefixes from a wordlist, appends the root domain, and feeds them into the validation engine.
"""

import os
from typing import Set
from subdomain_collector.core.base_collector import BaseCollector

class BruteForceCollector(BaseCollector):
    """
    Active brute force candidate generation module.
    Generates names based on a wordlist and leverages the core engine's DNS validation.
    """
    async def collect(self) -> Set[str]:
        subdomains: Set[str] = set()
        
        # Determine the wordlist path
        brute_config = self.config.get("brute_force", {})
        wordlist_path = brute_config.get("default_wordlist", "data/subdomains_common.txt")
        
        # Resolve paths relative to the tool root folder if it is relative
        if not os.path.isabs(wordlist_path):
            # Find the root project folder (two levels up from modules/)
            root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            wordlist_path = os.path.join(root_dir, wordlist_path)
            
        self.logger.info(f"Reading active dictionary prefixes from: {wordlist_path}")
        
        if not os.path.exists(wordlist_path):
            self.logger.error(f"Wordlist file not found: {wordlist_path}")
            return subdomains
            
        try:
            with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    prefix = line.strip().lower()
                    # Skip comments and empty lines
                    if not prefix or prefix.startswith("#"):
                        continue
                    # Append root domain
                    candidate = f"{prefix}.{self.domain}"
                    subdomains.add(candidate)
        except IOError as e:
            self.logger.error(f"Failed to read wordlist file: {str(e)}")
            
        self.logger.info(f"Generated {len(subdomains)} active dictionary candidates.")
        return subdomains
