import logging
from cvss import CVSS3, CVSS4
from typing import Dict, Any, Union, Optional

logger = logging.getLogger(__name__)

def parse_cvss_vector(vector: str) -> Optional[Dict[str, Any]]:
    """
    Parses a CVSS v3.1 or v4.0 vector string and calculates the scores.

    Args:
        vector (str): The CVSS vector string.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing the parsed scores,
                                  or None if the vector is invalid.
    """
    try:
        if vector.startswith("CVSS:3"):
            c = CVSS3(vector)
            return {
                "version": "3.x",
                "base_score": c.base_score,
                "temporal_score": c.temporal_score,
                "environmental_score": c.environmental_score,
                "severity": c.severities()[0],  # Get Base severity
                "vector": c.clean_vector()
            }
        elif vector.startswith("CVSS:4"):
            c = CVSS4(vector)
            return {
                 "version": "4.0",
                 "base_score": c.base_score,
                 # Temporal is folded into base in CVSS v4 metrics, but library supports it.
                 "threat_score": getattr(c, 'threat_score', None),
                 "environmental_score": getattr(c, 'environmental_score', None),
                 "severity": c.severities()[0],
                 "vector": c.clean_vector()
            }
        else:
            logger.error(f"Unsupported or invalid CVSS vector prefix: {vector}")
            return None

    except Exception as e:
        logger.error(f"Failed to parse CVSS vector '{vector}': {e}")
        return None
