import typer
from typing import Optional
from .parsers.nmap import NmapParser
import json

app = typer.Typer(help="Reconnaissance Analysis Toolkit")

@app.command()
def analyze(
    nmap_xml: str = typer.Argument(..., help="Path to Nmap XML output file"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output JSON file path")
):
    """Parses Nmap XML, normalizes data, and highlights critical findings."""
    typer.secho(f"[*] Analyzing Nmap scan: {nmap_xml}", fg=typer.colors.CYAN, bold=True)
    
    parser = NmapParser(nmap_xml)
    results = []
    
    try:
        for host in parser.parse():
            typer.secho(f"\n[+] Host: {host.ip_address}", fg=typer.colors.GREEN)
            for svc in host.services:
                alert = "[!]" if svc.is_cleartext else "   "
                color = typer.colors.RED if svc.is_cleartext else typer.colors.WHITE
                typer.secho(f"    {alert} Port {svc.port_id}/{svc.protocol} - {svc.name} {svc.product or ''}", fg=color)
            
            results.append(host.model_dump())
            
        if output:
            with open(output, "w") as f:
                json.dump(results, f, indent=4)
            typer.secho(f"\n[*] Results saved to {output}", fg=typer.colors.CYAN)
            
    except Exception as e:
        typer.secho(f"[X] Error parsing file: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
