"""
CLI Module
Handles command line arguments and parses them into a validated Config object.
"""
import argparse
import sys
from .config import Config
from pydantic import ValidationError

def parse_args() -> Config:
    parser = argparse.ArgumentParser(
        description="DirBruter: A professional async directory brute-forcing utility.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("-u", "--url", required=True, help="Target URL (e.g., https://example.com/)")
    parser.add_argument("-w", "--wordlist", required=True, help="Path to the wordlist file")
    parser.add_argument("-e", "--extensions", type=str, default="", help="Comma separated list of extensions to test (e.g., 'php,bak,txt')")
    parser.add_argument("-t", "--threads", type=int, default=50, help="Number of concurrent asynchronous workers")
    parser.add_argument("--timeout", type=int, default=10, help="HTTP request timeout in seconds")
    parser.add_argument("--retries", type=int, default=3, help="Number of retries for failed requests (e.g., 429, timeouts)")
    parser.add_argument("-a", "--user-agent", type=str, default="DirBruter/1.0 (Professional VAPT Tool)", help="Custom User-Agent string")
    parser.add_argument("-o", "--output", type=str, help="Path to save valid results (JSON/CSV based on extension)")
    parser.add_argument("--follow-redirects", action="store_true", help="Follow HTTP redirects (Use with caution to avoid scope bleed)")
    
    args = parser.parse_args()
    
    try:
        config = Config(
            target_url=args.url,
            wordlist_path=args.wordlist,
            extensions=args.extensions,
            threads=args.threads,
            timeout=args.timeout,
            retries=args.retries,
            user_agent=args.user_agent,
            output_file=args.output,
            allow_redirects=args.follow_redirects
        )
        return config
    except ValidationError as e:
        print(f"[-] Configuration Error:\n{e}")
        sys.exit(1)
