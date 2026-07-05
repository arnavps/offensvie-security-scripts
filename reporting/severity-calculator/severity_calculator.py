import sys
import argparse
import logging
from typing import Optional

from core import cvss_parser, business_logic
from utils import formatter

# Configure basic logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(
        description="Professional Severity Calculator for Vulnerability Reporting",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "vector",
        help="The CVSS v3.1 or v4.0 vector string\n(e.g., 'CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H')"
    )
    
    parser.add_argument(
        "-c", "--criticality",
        choices=["low", "medium", "high", "critical"],
        default="medium",
        help="Asset criticality (default: medium)"
    )
    
    parser.add_argument(
        "-j", "--json",
        action="store_true",
        help="Output results in JSON format"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print verbose output including raw JSON (when not in JSON mode)"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)

    # 1. Parse the CVSS Vector
    logger.info(f"Parsing vector: {args.vector}")
    parsed_cvss = cvss_parser.parse_cvss_vector(args.vector)
    
    if not parsed_cvss:
        print("Error: Invalid or unsupported CVSS vector provided.", file=sys.stderr)
        sys.exit(1)

    # 2. Apply Business Logic Adjustments
    logger.info(f"Applying business context. Criticality: {args.criticality}")
    base_score = parsed_cvss.get("base_score", 0.0)
    adjusted_score = business_logic.adjust_score_by_business_context(base_score, args.criticality)
    adjusted_severity = business_logic.determine_adjusted_severity(adjusted_score)

    # 3. Prepare Results Dictionary
    results = {
        **parsed_cvss,
        "business_context": {
            "criticality": args.criticality
        },
        "adjusted_score": adjusted_score,
        "adjusted_severity": adjusted_severity
    }

    # 4. Output Results
    if args.json:
        print(formatter.format_json_output(results))
    else:
        formatter.format_terminal_output(results, verbose=args.verbose)

if __name__ == "__main__":
    main()
