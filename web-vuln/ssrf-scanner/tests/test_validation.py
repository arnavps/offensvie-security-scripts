"""
SSRF Validation Test Suite

This module provides unit and integration tests to verify the correctness of the
SSRFValidator class and the DNS Rebinding mitigation clients.
"""

import socket
from unittest.mock import patch
import pytest
import httpx
from lib.validator import SSRFValidator, DNSRebindingSafeClient
from app.middleware import DNSRebindingSafeAsyncTransport, SSRFPreventionTransport


@pytest.fixture
def default_validator():
    return SSRFValidator()


def test_valid_public_urls(default_validator):
    """
    Verifies that standard, safe public URLs resolve and pass validation.
    """
    valid_urls = [
        "https://www.google.com",
        "http://example.com/index.html",
        "https://github.com/features",
    ]
    for url in valid_urls:
        is_valid, reason = default_validator.validate_url(url)
        assert is_valid, f"Failed on safe URL: {url}. Reason: {reason}"


def test_blocked_schemes(default_validator):
    """
    Verifies that schemes other than http and https are rejected.
    """
    invalid_urls = [
        "file:///etc/passwd",
        "gopher://127.0.0.1:70/11",
        "dict://127.0.0.1:11211/stat",
        "ftp://example.com/file.txt",
        "tftp://example.com/file",
        "php://filter/read=convert.base64-encode/resource=index.php",
    ]
    for url in invalid_urls:
        is_valid, reason = default_validator.validate_url(url)
        assert not is_valid, f"Failed to block unsafe scheme URL: {url}"
        assert "scheme" in reason.lower()


def test_blocked_ports(default_validator):
    """
    Verifies that connection ports outside the permitted list (80, 443) are blocked.
    """
    validator = SSRFValidator(allowed_ports={80, 443})
    invalid_port_urls = [
        "http://example.com:22",
        "http://example.com:8080/dashboard",
        "https://example.com:8443/api",
    ]
    for url in invalid_port_urls:
        is_valid, reason = validator.validate_url(url)
        assert not is_valid, f"Failed to block restricted port: {url}"
        assert "port" in reason.lower()


def test_blocked_private_subnets(default_validator):
    """
    Verifies that private, loopback, and cloud metadata IP ranges are blocked.
    """
    private_urls = [
        "http://127.0.0.1",
        "http://10.0.0.1/admin",
        "http://172.16.5.5",
        "http://192.168.1.100",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]",
        "http://[fe80::1]",
    ]
    for url in private_urls:
        is_valid, reason = default_validator.validate_url(url)
        assert not is_valid, f"Failed to block private destination: {url}"
        assert any(term in reason.lower() for term in ["restricted", "private", "loopback", "metadata", "blocked"])


def test_whitelisted_hosts():
    """
    Verifies that hosts explicitly defined in the allowed list bypass IP resolution checks.
    """
    validator = SSRFValidator(allowed_hosts={"internal.corp", "localhost.localdomain"})
    
    # internal.corp resolves to a private range locally but is explicitly allowed
    is_valid, reason = validator.validate_url("http://internal.corp/status")
    assert is_valid
    assert "explicitly allowed" in reason.lower()


@patch("socket.getaddrinfo")
def test_dns_rebinding_prevention_rewriting(mock_getaddrinfo):
    """
    Tests that the DNSRebindingSafeClient correctly resolves and rewrites
    the outbound request destination URL to lock onto the validated IP.
    """
    # Mock DNS resolution to return a safe public IP (93.184.216.34)
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", 80))
    ]

    client = DNSRebindingSafeClient()
    safe_url, headers = client.make_safe_http_request_details("http://example.com/test-endpoint")
    
    assert "93.184.216.34" in safe_url
    assert headers["Host"] == "example.com"


import asyncio

@patch("socket.getaddrinfo")
def test_safe_async_transport_blocks_private_dns(mock_getaddrinfo):
    """
    Verifies that the DNSRebindingSafeAsyncTransport raises a ConnectError
    if a domain name resolves to a private IP (resolving at transport runtime).
    """
    # Mock domain resolution to return an internal IP address (192.168.1.5)
    mock_getaddrinfo.return_value = [
        (socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("192.168.1.5", 80))
    ]

    transport = DNSRebindingSafeAsyncTransport()
    request = httpx.Request("GET", "http://malicious-domain.com/data")
    
    with pytest.raises(httpx.ConnectError) as exc_info:
        asyncio.run(transport.handle_async_request(request))
        
    assert "restricted IP" in str(exc_info.value) or "validation blocked" in str(exc_info.value)
