"""
Custom logger implementation using Rich for beautiful terminal output.
"""
import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

# Define a custom theme for our offensive security tool
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "danger": "bold red",
    "success": "bold green"
})

console = Console(theme=custom_theme)

def setup_logger(verbose: bool = False) -> logging.Logger:
    """
    Configures and returns a rich logger instance.
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # We use a clean format without the full path unless debugging
    format_str = "%(message)s"
    
    logging.basicConfig(
        level=level,
        format=format_str,
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=verbose)]
    )
    
    return logging.getLogger("jwt_analyzer")

logger = logging.getLogger("jwt_analyzer")
