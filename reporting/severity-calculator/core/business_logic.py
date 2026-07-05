import logging

logger = logging.getLogger(__name__)

# Basic multipliers for demonstration purposes
CRITICALITY_MULTIPLIERS = {
    "low": 0.8,
    "medium": 1.0,
    "high": 1.2,
    "critical": 1.5
}

def adjust_score_by_business_context(base_score: float, criticality: str = "medium") -> float:
    """
    Adjusts a CVSS base score using a business criticality multiplier.

    Args:
        base_score (float): The base CVSS score.
        criticality (str): The asset criticality level ('low', 'medium', 'high', 'critical').

    Returns:
        float: The adjusted score, capped at 10.0.
    """
    multiplier = float(CRITICALITY_MULTIPLIERS.get(criticality.lower(), 1.0))
    
    if multiplier == 1.0 and criticality.lower() != "medium":
        logger.warning(f"Unknown criticality level '{criticality}', defaulting to medium (1.0x).")

    adjusted_score = float(base_score) * multiplier
    
    # Ensure score doesn't exceed 10.0
    return min(round(adjusted_score, 1), 10.0)

def determine_adjusted_severity(score: float) -> str:
    """
    Maps a numeric score to a qualitative severity rating.
    """
    if score == 0.0:
        return "None"
    elif 0.1 <= score <= 3.9:
        return "Low"
    elif 4.0 <= score <= 6.9:
        return "Medium"
    elif 7.0 <= score <= 8.9:
        return "High"
    elif 9.0 <= score <= 10.0:
        return "Critical"
    else:
        return "Unknown"
