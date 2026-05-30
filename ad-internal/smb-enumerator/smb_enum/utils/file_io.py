import json
from typing import List, Dict, Any

def export_to_json(results: List[Dict[str, Any]], filepath: str) -> None:
    """
    Exports a list of dictionaries to a JSON file.
    
    Args:
        results: List of result dictionaries.
        filepath: Path to the output JSON file.
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

def parse_targets(target_strings: List[str]) -> List[str]:
    """
    Parses a list of target strings which could be individual IPs, hostnames, 
    CIDR notations (like 192.168.1.0/24), or file paths containing targets.
    Returns a flattened list of individual IP strings/hostnames.
    """
    import os
    import netaddr
    
    final_targets = set()
    
    for t in target_strings:
        # Check if it's a file
        if os.path.isfile(t):
            with open(t, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Process each line from the file recursively
                        final_targets.update(parse_targets([line]))
            continue
            
        # Check if it's a CIDR
        if '/' in t:
            try:
                network = netaddr.IPNetwork(t)
                for ip in network.iter_hosts():
                    final_targets.add(str(ip))
            except netaddr.AddrFormatError:
                # Fallback to string just in case it's some weird hostname
                final_targets.add(t)
        else:
            # Individual IP or Hostname
            final_targets.add(t)
            
    return list(final_targets)
