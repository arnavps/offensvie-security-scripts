"""
Vulnerability and anomaly detection engine.
Analyzes the decoded JWT parts to flag security risks.
"""

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from ..utils.config import AnalyzerConfig


class Vulnerability(BaseModel):
    title: str
    severity: str
    description: str


class AnalyzerResult(BaseModel):
    vulnerabilities: List[Vulnerability] = []
    sensitive_data_exposed: Dict[str, Any] = {}
    is_expired: bool = False
    is_not_yet_valid: bool = False
    algorithm: str = "unknown"
    has_signature: bool = False


def analyze_jwt(header: Dict[str, Any], payload: Dict[str, Any], signature: Optional[str], config: AnalyzerConfig) -> AnalyzerResult:
    """
    Performs security checks on the decoded JWT components.
    """
    result = AnalyzerResult()
    
    # 1. Check Algorithm
    alg = header.get("alg", "unknown").lower()
    result.algorithm = alg
    
    if alg in [a.lower() for a in config.weak_algorithms]:
        result.vulnerabilities.append(
            Vulnerability(
                title=f"Weak or None Algorithm: {alg}",
                severity="CRITICAL",
                description="The token uses a weak algorithm or 'none', allowing signature bypass."
            )
        )
        
    # 2. Check Signature presence
    if signature:
        result.has_signature = True
    else:
        result.vulnerabilities.append(
            Vulnerability(
                title="Missing Signature",
                severity="HIGH",
                description="The token has no signature and may be accepted without verification."
            )
        )
        
    # 3. Check for sensitive data exposure
    for key, value in payload.items():
        # Check against wordlist (case insensitive partial match could be added, but exact match for now)
        if any(sensitive_key.lower() in key.lower() for sensitive_key in config.sensitive_keys):
            result.sensitive_data_exposed[key] = value

    if result.sensitive_data_exposed:
        result.vulnerabilities.append(
            Vulnerability(
                title="Sensitive Data Exposure",
                severity="MEDIUM",
                description="The payload contains claims that might leak sensitive information or PII."
            )
        )
        
    # 4. Check expiration and timestamps
    current_time = int(time.time())
    
    exp = payload.get("exp")
    if exp and isinstance(exp, (int, float)):
        if exp < current_time:
            result.is_expired = True
            
    nbf = payload.get("nbf")
    if nbf and isinstance(nbf, (int, float)):
        if nbf > current_time:
            result.is_not_yet_valid = True
            
    if not exp:
        result.vulnerabilities.append(
            Vulnerability(
                title="Missing Expiration Claim (exp)",
                severity="LOW",
                description="The token does not expire, which can lead to permanent session hijacking."
            )
        )
            
    return result
