"""
Core decoding logic for JWTs.
"""

import base64
import json
import re
from typing import Dict, Any, Tuple, Optional

from .exceptions import InvalidJWTFormatError, DecodeError


def _add_base64_padding(b64_string: str) -> str:
    """
    Adds missing Base64 padding. Python's base64 parser requires standard padding.
    """
    padding = len(b64_string) % 4
    if padding == 1:
        # A valid base64url string shouldn't have a length % 4 == 1
        raise DecodeError("Invalid base64url string length.")
    elif padding > 0:
        b64_string += "=" * (4 - padding)
    return b64_string


def _decode_b64url_json(b64_string: str) -> Dict[str, Any]:
    """
    Decodes a base64url encoded JSON string.
    """
    try:
        # Standardize to base64url characters
        b64_string = b64_string.replace("-", "+").replace("_", "/")
        padded = _add_base64_padding(b64_string)
        decoded_bytes = base64.b64decode(padded)
        return json.loads(decoded_bytes.decode('utf-8'))
    except (base64.binascii.Error, UnicodeDecodeError, json.JSONDecodeError) as e:
        raise DecodeError(f"Failed to decode segment: {str(e)}")


def parse_jwt(token: str) -> Tuple[Dict[str, Any], Dict[str, Any], Optional[str]]:
    """
    Safely parses a JWT without verifying the signature.
    
    Args:
        token (str): The raw JWT string.
        
    Returns:
        Tuple containing (header_dict, payload_dict, signature_string)
        
    Raises:
        InvalidJWTFormatError: If the structure doesn't match a JWT.
        DecodeError: If decoding fails.
    """
    token = token.strip()
    
    # Ensure it's a basic JWT structure (two or three parts separated by dots)
    if not re.match(r"^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]*)?$", token):
        raise InvalidJWTFormatError("Token does not match the standard JWT format.")
        
    parts = token.split('.')
    
    header = _decode_b64url_json(parts[0])
    payload = _decode_b64url_json(parts[1])
    
    signature = parts[2] if len(parts) == 3 and parts[2] else None
    
    return header, payload, signature
