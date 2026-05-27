import pytest
from jwt_analyzer.core.decoder import parse_jwt, _add_base64_padding
from jwt_analyzer.core.exceptions import InvalidJWTFormatError, DecodeError

def test_add_base64_padding():
    # 'a' is length 1, not valid in base64url really but logic-wise padding=1 throws DecodeError
    with pytest.raises(DecodeError):
        _add_base64_padding("a")
    
    assert _add_base64_padding("ab") == "ab=="
    assert _add_base64_padding("abc") == "abc="
    assert _add_base64_padding("abcd") == "abcd"

def test_parse_jwt_valid():
    # {"alg":"HS256","typ":"JWT"}.{"sub":"1234567890","name":"John Doe","iat":1516239022}
    # Note: padding is missing intentionally to test our fix
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    header, payload, signature = parse_jwt(token)
    
    assert header["alg"] == "HS256"
    assert payload["name"] == "John Doe"
    assert signature == "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

def test_parse_jwt_invalid_format():
    with pytest.raises(InvalidJWTFormatError):
        parse_jwt("not.a.valid.jwt.string")
        
def test_parse_jwt_no_signature():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ"
    header, payload, signature = parse_jwt(token)
    
    assert header["alg"] == "HS256"
    assert signature is None

def test_parse_jwt_trailing_dot():
    token = "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIn0."
    header, payload, signature = parse_jwt(token)
    
    assert header["alg"] == "none"
    assert signature is None
