"""
Custom colored console logging and formatted output utility for the Subdomain Collector.
Provides clean terminal UI markers like [+], [-], [*], and [!] for status reporting.
"""

import sys
import logging

class ColoredFormatter(logging.Formatter):
    # ANSI escape sequences for terminal colors
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Colors
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"

    FORMATS = {
        logging.DEBUG: f"{GRAY}[*] DEBUG: %(message)s{RESET}",
        logging.INFO: f"{GREEN}[+] %(message)s{RESET}",
        logging.WARNING: f"{YELLOW}[!] WARNING: %(message)s{RESET}",
        logging.ERROR: f"{RED}[-] ERROR: %(message)s{RESET}",
        logging.CRITICAL: f"{RED}{BOLD}[!!] CRITICAL: %(message)s{RESET}"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, "%(message)s")
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(name: str = "SubdomainCollector", level: int = logging.INFO) -> logging.Logger:
    """
    Bootstraps the logger with standard output colored formatting.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers if setup_logger is called multiple times
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter())
        logger.addHandler(console_handler)
        
    return logger
