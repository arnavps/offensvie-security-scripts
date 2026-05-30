from rich.table import Table
from typing import List, Dict, Any

def generate_results_table(results: List[Dict[str, Any]]) -> Table:
    """
    Takes a list of share result dictionaries and returns a formatted rich Table.
    
    Expected dict structure:
    {
        "host": "192.168.1.10",
        "share": "C$",
        "read": True,
        "write": False,
        "remark": "Default share"
    }
    """
    table = Table(title="SMB Share Enumeration Results", show_header=True, header_style="bold magenta")
    table.add_column("Host", style="cyan", no_wrap=True)
    table.add_column("Share Name", style="white")
    table.add_column("Read Access", justify="center")
    table.add_column("Write Access", justify="center")
    table.add_column("Remark", style="dim")
    
    for res in results:
        # Format Read Access
        read_text = "[green]Yes[/green]" if res.get("read") else "[red]No[/red]"
        
        # Format Write Access
        write_value = res.get("write")
        if write_value is True:
            write_text = "[bold red]Yes[/bold red]" # Write access is highly critical!
        elif write_value is False:
            write_text = "[green]No[/green]"
        else:
            write_text = "[dim]N/A[/dim]" # Not checked
            
        table.add_row(
            res.get("host", ""),
            res.get("share", ""),
            read_text,
            write_text,
            res.get("remark", "")
        )
        
    return table
