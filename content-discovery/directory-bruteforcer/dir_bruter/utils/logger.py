import logging
from rich.logging import RichHandler

def setup_logger():
    """Configure centralized logging using rich for console output."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)]
    )
    # Suppress httpx info logs to keep output clean
    logging.getLogger("httpx").setLevel(logging.WARNING)
    return logging.getLogger("dirbrute")

logger = setup_logger()
