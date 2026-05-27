"""
Command Line Interface for the JWT Analyzer.
"""
import sys
import json
import typer
from typing import Optional
from pathlib import Path
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from .core.decoder import parse_jwt
from .core.analyzer import analyze_jwt
from .core.exceptions import JWTAnalyzerError
from .utils.logger import setup_logger, console
from .utils.config import load_config

app = typer.Typer(help="Professional JWT Analyzer for Offensive Security.", add_completion=False)

def print_banner():
    console.print("[bold cyan]JWT Analyzer v0.1.0[/bold cyan]")
    console.print("Offensive Security Utility\n")

@app.command()
def analyze(
    token: Optional[str] = typer.Option(None, "--token", "-t", help="Raw JWT string to analyze."),
    file: Optional[Path] = typer.Option(None, "--file", "-f", help="File containing the JWT."),
    config_file: str = typer.Option("config/settings.yaml", "--config", "-c", help="Path to config file."),
    export_json: Optional[Path] = typer.Option(None, "--export-json", "-e", help="Export results to a JSON file."),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging.")
):
    """
    Decodes and analyzes a JWT for security misconfigurations.
    """
    logger = setup_logger(verbose)
    
    # Handle input (stdin, file, or token arg)
    raw_token = ""
    if token:
        raw_token = token
    elif file:
        try:
            raw_token = file.read_text().strip()
        except Exception as e:
            logger.error(f"Failed to read file {file}: {e}")
            raise typer.Exit(code=1)
    elif not sys.stdin.isatty():
        # Read from stdin if piped
        raw_token = sys.stdin.read().strip()
        
    if not raw_token:
        logger.error("No JWT provided. Use --token, --file, or pipe from stdin.")
        raise typer.Exit(code=1)
        
    print_banner()
    
    # Load config
    config = load_config(config_file)
    logger.debug(f"Loaded config: {config}")
    
    try:
        # Parse JWT
        logger.info("Decoding JWT...")
        header, payload, signature = parse_jwt(raw_token)
        
        # Analyze JWT
        logger.info("Analyzing JWT...")
        result = analyze_jwt(header, payload, signature, config)
        
        # Display Results
        
        # Print Header and Payload as pretty JSON
        console.print(Panel(Syntax(json.dumps(header, indent=2), "json", theme="monokai", background_color="default"), title="[bold green]Header[/bold green]"))
        console.print(Panel(Syntax(json.dumps(payload, indent=2), "json", theme="monokai", background_color="default"), title="[bold green]Payload[/bold green]"))
        
        # Print Vulnerability Table
        if result.vulnerabilities:
            table = Table(title="[bold red]Vulnerabilities Found[/bold red]")
            table.add_column("Severity", style="bold")
            table.add_column("Title", style="cyan")
            table.add_column("Description")
            
            for vuln in result.vulnerabilities:
                color = "red" if vuln.severity == "CRITICAL" else "yellow" if vuln.severity == "HIGH" else "magenta"
                table.add_row(f"[{color}]{vuln.severity}[/]", vuln.title, vuln.description)
                
            console.print(table)
        else:
            console.print("\n[bold green][+] No obvious vulnerabilities found based on current rules.[/bold green]")
            
        # Highlight specific flags
        if result.is_expired:
            console.print("[warning][!] The token is expired.[/warning]")
        if result.is_not_yet_valid:
            console.print("[warning][!] The token is not yet valid (nbf).[/warning]")
            
        if result.sensitive_data_exposed:
            console.print("\n[warning]Potential Sensitive Data Exposed:[/warning]")
            for k, v in result.sensitive_data_exposed.items():
                console.print(f"  - [cyan]{k}[/cyan]: {v}")
                
        # Handle Export
        if export_json:
            export_data = {
                "raw_token": raw_token,
                "header": header,
                "payload": payload,
                "has_signature": result.has_signature,
                "analysis": result.model_dump()
            }
            with open(export_json, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
            logger.info(f"\n[+] Results exported to {export_json}")

    except JWTAnalyzerError as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise typer.Exit(code=1)
    except Exception as e:
        logger.exception(f"An unexpected error occurred: {str(e)}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
