"""
Custom exceptions for the SMB Enumerator.
"""

class SMBEnumException(Exception):
    """Base exception for all SMB Enumerator errors."""
    pass

class AuthenticationError(SMBEnumException):
    """Raised when authentication fails."""
    pass

class HostUnreachableError(SMBEnumException):
    """Raised when a host cannot be reached (e.g., timeout)."""
    pass

class ConnectionRefusedError(SMBEnumException):
    """Raised when connection is actively refused (e.g., port closed)."""
    pass

class ConfigurationError(SMBEnumException):
    """Raised when there is a configuration error."""
    pass
