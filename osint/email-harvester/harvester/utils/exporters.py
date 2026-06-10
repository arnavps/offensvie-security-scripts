import csv
import json
import os
from typing import List

from ..core.models import EmailResult
from ..utils.logger import logger


def export_json(results: List[EmailResult], filepath: str):
    """Exports results to a JSON file."""
    try:
        # Pydantic model_dump handles the serialization cleanly
        data = [r.model_dump() for r in results]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        logger.info(f"[green][+][/green] Successfully exported JSON to: {filepath}")
    except Exception as e:
        logger.error(f"[red][!][/red] Failed to export JSON: {e}")


def export_csv(results: List[EmailResult], filepath: str):
    """Exports results to a CSV file."""
    try:
        if not results:
            logger.warning("No results to export to CSV.")
            return

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            # Get field names from the first Pydantic model
            fieldnames = list(results[0].model_dump().keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for r in results:
                writer.writerow(r.model_dump())
                
        logger.info(f"[green][+][/green] Successfully exported CSV to: {filepath}")
    except Exception as e:
        logger.error(f"[red][!][/red] Failed to export CSV: {e}")
