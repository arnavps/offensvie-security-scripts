import json
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def format_terminal_output(results: Dict[str, Any], verbose: bool = False):
    """
    Formats the calculation results into a visually appealing terminal table using Rich.
    """
    table = Table(title="Severity Calculation Results", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="dim", width=25)
    table.add_column("Value")

    table.add_row("CVSS Version", results.get("version", "N/A"))
    table.add_row("Vector", results.get("vector", "N/A"))
    table.add_row("Base Score", str(results.get("base_score", "N/A")))
    table.add_row("Original Severity", results.get("severity", "N/A"))
    
    table.add_section()
    table.add_row("Asset Criticality", results.get("business_context", {}).get("criticality", "medium").title())
    table.add_row("Adjusted Risk Score", str(results.get("adjusted_score", "N/A")), style="bold red")
    table.add_row("Adjusted Risk Rating", results.get("adjusted_severity", "N/A"), style="bold red")

    console.print(table)
    
    if verbose:
         console.print(Panel(json.dumps(results, indent=2), title="Raw JSON Data", expand=False))

def format_json_output(results: Dict[str, Any]) -> str:
    """
    Returns the calculation results as a JSON string for integration into other tools.
    """
    return json.dumps(results, indent=4)
