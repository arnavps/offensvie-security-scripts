import logging
import sys

from rich.logging import RichHandler


def setup_logger(verbose: bool = False) -> logging.Logger:
    """
    Configures a structured logger using Rich for beautiful terminal output.
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Configure the standard python logging module to use RichHandler
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True, show_path=verbose)]
    )

    log = logging.getLogger("harvester")
    # Prevent propagation to the root logger to avoid double-logging if other modules misbehave
    log.propagate = False
    
    # Ensure our specific logger also has the handler if propagation is off
    if not log.handlers:
        log.addHandler(RichHandler(rich_tracebacks=True, markup=True, show_path=verbose))

    return log

# Export a default instance
logger = logging.getLogger("harvester")
