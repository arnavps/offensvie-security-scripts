import typer
import sys
from typing import List, Optional
from rich.console import Console

from smb_enum.config import ScanConfig
from smb_enum.utils.logger import setup_logger
from smb_enum.utils.file_io import parse_targets, export_to_json
from smb_enum.utils.formatters import generate_results_table
from smb_enum.core.scanner import Scanner

# Typer app initialization
app = typer.Typer(
    help="Professional SMB Share Enumerator for VAPT workflows.",
    add_completion=False
)
console = Console()

@app.command()
def main(
    targets: List[str] = typer.Argument(
        ..., 
        help="IP, CIDR, Hostname, or path to file containing targets."
    ),
    domain: str = typer.Option("", "-d", "--domain", help="Active Directory Domain."),
    username: str = typer.Option("", "-u", "--username", help="Username for authentication (Leave empty for Null Session)."),
    password: str = typer.Option("", "-p", "--password", help="Password for authentication."),
    hashes: str = typer.Option("", "-H", "--hashes", help="NTLM hashes, format LM:NT or NT."),
    port: int = typer.Option(445, "--port", help="SMB Port."),
    threads: int = typer.Option(20, "-t", "--threads", help="Number of concurrent threads.", min=1, max=100),
    timeout: float = typer.Option(3.0, "--timeout", help="Socket timeout in seconds."),
    json_out: Optional[str] = typer.Option(None, "-oJ", "--json", help="Path to save results as JSON."),
    check_write: bool = typer.Option(False, "-w", "--check-write", help="Attempt to create a temp file to verify Write Access."),
    verbose: bool = typer.Option(False, "-v", "--verbose", help="Enable verbose debug logging.")
):
    """
    Automates the discovery of active network shares across a range of IP addresses 
    or domain hosts, checking for Read/Write access using specified credentials or Null sessions.
    """
    
    # 1. Setup Logging
    logger = setup_logger(verbose=verbose)
    
    # 2. Build and Validate Configuration
    try:
        config = ScanConfig(
            targets=targets,
            domain=domain,
            username=username,
            password=password,
            hash=hashes,
            port=port,
            timeout=timeout,
            threads=threads,
            json_out=json_out,
            check_write=check_write
        )
    except Exception as e:
        console.print(f"[bold red]Configuration Error:[/bold red] {e}")
        raise typer.Exit(code=1)
        
    if config.is_null_session:
        logger.info("[bold yellow]No username provided. Running in Null Session mode.[/bold yellow]", extra={"markup": True})
        
    # 3. Parse Targets
    parsed_ips = parse_targets(config.targets)
    if not parsed_ips:
        console.print("[bold red]No valid targets found to scan.[/bold red]")
        raise typer.Exit(code=1)
        
    # 4. Execute Scan
    scanner = Scanner(config)
    
    try:
        results = scanner.run(parsed_ips)
    except KeyboardInterrupt:
        logger.warning("Scan aborted by user.")
        results = scanner.results # Save whatever we got so far
        
    # 5. Output Processing
    if not results:
        console.print("[yellow]No accessible shares were found across the targets.[/yellow]")
        raise typer.Exit(code=0)
        
    # Print Table
    table = generate_results_table(results)
    console.print("\n")
    console.print(table)
    
    # Export JSON
    if config.json_out:
        try:
            export_to_json(results, config.json_out)
            logger.info(f"Results exported to {config.json_out}")
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")

if __name__ == "__main__":
    app()
