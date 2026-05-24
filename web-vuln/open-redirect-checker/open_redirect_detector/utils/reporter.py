"""
Export results module to format and write reports to disk in JSON format.
"""
import json
import os
from typing import Dict, Any, List

class Exporter:
    """
    Saves security inspection metadata and findings.
    """
    @staticmethod
    def export_json(results: List[Dict[str, Any]], output_path: str) -> bool:
        """
        Exports the scanning result dictionary to a JSON file.
        """
        if not output_path:
            return False
            
        try:
            # Create directories dynamically if missing
            dir_name = os.path.dirname(os.path.abspath(output_path))
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
                
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=4)
            return True
        except Exception:
            return False
