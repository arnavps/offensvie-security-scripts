import httpx
from rich.console import Console

console = Console()

def format_hit(url: str, response: httpx.Response):
    """
    Formats a valid hit for terminal output.
    Colors based on status code groups (e.g., 2xx green, 3xx cyan, 4xx yellow).
    """
    status = response.status_code
    size = len(response.content)
    
    if 200 <= status < 300:
        color = "green"
    elif 300 <= status < 400:
        color = "cyan"
    elif 400 <= status < 500:
        color = "yellow"
    else:
        color = "red"
        
    console.print(f"[{color}][{status}][/{color}] {url} (Size: {size})")
