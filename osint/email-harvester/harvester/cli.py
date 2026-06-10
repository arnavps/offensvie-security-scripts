import asyncio
import sys

import typer
from rich.console import Console

from .core.engine import HarvesterEngine
from .utils.exporters import export_csv, export_json
from .utils.logger import setup_logger

app = typer.Typer(
    help="Professional OSINT tool for harvesting employee emails associated with a target domain.",
    no_args_is_help=True
)

console = Console()

@app.command()
def run(
    domain: str = typer.Option(..., "--domain", "-d", help="Target domain (e.g., example.com)"),
    timeout: int = typer.Option(15, "--timeout", "-t", help="HTTP timeout in seconds"),
    json_export: str = typer.Option(None, "--json", help="Export results to a JSON file"),
    csv_export: str = typer.Option(None, "--csv", help="Export results to a CSV file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose debug logging")
):
    """
    Executes the email harvesting workflow.
    """
    console.print(f"[bold red]WARNING:[/bold red] This tool is for authorized security testing and OSINT research only.")
    console.print("Do not use against targets without explicit permission.\n")
    
    # Initialize structured logging
    logger = setup_logger(verbose=verbose)
    
    try:
        engine = HarvesterEngine(target_domain=domain, timeout=timeout)
        
        # Run the async event loop
        # Typer is synchronous by default, so we use asyncio.run to execute our async engine
        results = asyncio.run(engine.execute())
        
        if not results:
            console.print("[yellow]No emails found for the target domain.[/yellow]")
            return
            
        console.print(f"\n[bold green]Results for {domain}[/bold green]")
        for res in results:
            console.print(f" - [cyan]{res.email}[/cyan] (Source: {res.source})")
            
        if json_export:
            export_json(results, json_export)
            
        if csv_export:
            export_csv(results, csv_export)
            
    except ValueError as e:
        # Catch Pydantic validation errors (e.g., invalid domain format)
        logger.error(f"Configuration Error: {e}")
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        logger.warning("\nExecution interrupted by user. Exiting gracefully.")
        sys.exit(0)
    except Exception as e:
        logger.exception("An unexpected error occurred.")
        sys.exit(1)

def main():
    """Entry point for the CLI."""
    app()
