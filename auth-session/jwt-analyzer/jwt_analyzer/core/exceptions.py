"""
Custom exceptions for the JWT Analyzer.
"""

class JWTAnalyzerError(Exception):
    """Base exception for all JWT Analyzer errors."""
    pass

class InvalidJWTFormatError(JWTAnalyzerError):
    """Raised when the input is not a structurally valid JWT."""
    pass

class DecodeError(JWTAnalyzerError):
    """Raised when there is an error decoding the JWT (e.g., bad Base64 or invalid JSON)."""
    pass
