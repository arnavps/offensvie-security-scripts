import logging
from rich.logging import RichHandler

def setup_logger(verbose: bool = False) -> logging.Logger:
    """
    Configures and returns a centralized logger using rich for console output.
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure the standard python logging module to use RichHandler
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                markup=True,
                show_path=False,  # Don't show the file path in standard output (too noisy for a CLI tool)
                log_time_format="[%X]"
            )
        ]
    )
    
    # Suppress verbose logging from impacket unless we are in debug mode
    impacket_logger = logging.getLogger('impacket')
    if not verbose:
        impacket_logger.setLevel(logging.WARNING)
        
    return logging.getLogger("smb_enum")
