"""
SSRF Prevention Middleware and Safe Clients

This module provides integrations and wrappers for HTTP clients (like HTTPX) to
automatically validate outgoing requests, log telemetry for blocked attempts, and
implement mitigations against DNS Rebinding attacks at the client/transport layer.
"""

import logging
import time
from typing import Any, Dict, Generator, Optional
import httpx
from lib.validator import SSRFValidator

logger = logging.getLogger("ssrf_mitigation.middleware")


class SSRFPreventionTransport(httpx.HTTPTransport):
    """
    Custom HTTPX Transport that intercepts outgoing HTTP requests and runs them
    through the SSRFValidator before connection establishment.
    """

    def __init__(self, validator: Optional[SSRFValidator] = None, **kwargs: Any):
        self.validator = validator or SSRFValidator()
        super().__init__(**kwargs)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        """
        Sync request handler interceptor.
        """
        url_str = str(request.url)
        is_valid, reason = self.validator.validate_url(url_str)
        
        if not is_valid:
            self._log_blocked_attempt(request, reason)
            raise httpx.ConnectError(
                f"Blocked outbound request by SSRF Prevention Transport: {reason}",
                request=request
            )
            
        return super().handle_request(request)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        """
        Async request handler interceptor.
        """
        url_str = str(request.url)
        is_valid, reason = self.validator.validate_url(url_str)
        
        if not is_valid:
            self._log_blocked_attempt(request, reason)
            raise httpx.ConnectError(
                f"Blocked outbound request by SSRF Prevention Transport: {reason}",
                request=request
            )
            
        return await super().handle_async_request(request)

    def _log_blocked_attempt(self, request: httpx.Request, reason: str) -> None:
        """
        Emits structured telemetry for security monitoring and SIEM digestion.
        """
        event = {
            "timestamp": time.time(),
            "event_type": "SSRF_PREVENTED",
            "target_url": str(request.url),
            "target_host": request.url.host,
            "target_port": request.url.port,
            "block_reason": reason,
            "http_method": request.method,
        }
        logger.warning(
            "SSRF Security Violation Blocked: Outbound request to %s was blocked. Reason: %s",
            event["target_url"],
            reason,
            extra={"security_telemetry": event}
        )


class DNSRebindingSafeAsyncTransport(httpx.AsyncHTTPTransport):
    """
    An Advanced HTTPX Async Transport that prevents DNS Rebinding attacks by
    pre-resolving the host and rewriting requests to route directly to the validated IP.
    """

    def __init__(self, validator: Optional[SSRFValidator] = None, **kwargs: Any):
        self.validator = validator or SSRFValidator()
        super().__init__(**kwargs)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        url = request.url
        hostname = url.host
        
        # Step 1: Pre-validate host/URL configuration
        is_valid, reason = self.validator.validate_url(str(url))
        if not is_valid:
            raise httpx.ConnectError(f"SSRF validation blocked request: {reason}", request=request)

        # Skip DNS rewriting if it's already an IP address
        try:
            # Check if hostname is an IP (will not throw error if it is)
            import ipaddress
            ipaddress.ip_address(hostname.strip("[]"))
            return await super().handle_async_request(request)
        except ValueError:
            pass

        # Step 2: Resolve hostname to IPs and select first validated IP
        resolved_ips = self.validator.resolve_hostname(hostname)
        if not resolved_ips:
            raise httpx.ConnectError(f"Failed to resolve host '{hostname}'", request=request)

        # Enforce that all resolved IPs are safe
        for ip in resolved_ips:
            is_safe, ip_reason = self.validator.is_safe_ip(ip)
            if not is_safe:
                raise httpx.ConnectError(f"Resolved restricted IP address '{ip}': {ip_reason}", request=request)

        target_ip = str(resolved_ips[0])
        if ":" in target_ip and not target_ip.startswith("["):
            formatted_ip = f"[{target_ip}]"
        else:
            formatted_ip = target_ip

        # Step 3: Mutate Request URL to point directly to IP, bypassing subsequent DNS lookup
        port_suffix = f":{url.port}" if url.port else ""
        rewritten_netloc = f"{formatted_ip}{port_suffix}".encode("utf-8")
        
        # Inject Host header to preserve routing and HTTP certificate validation
        request.headers["Host"] = hostname
        request.url = httpx.URL(
            scheme=url.scheme.encode("utf-8"),
            netloc=rewritten_netloc,
            path=url.path.encode("utf-8"),
            query=url.query or None,
            fragment=url.fragment or None
        )

        logger.debug("Rewrote request destination from %s to %s for DNS rebinding protection.", hostname, target_ip)
        return await super().handle_async_request(request)


# =====================================================================
# FACTORY FUNCTIONS FOR SECURE CLIENTS
# =====================================================================

def get_safe_async_client(validator: Optional[SSRFValidator] = None) -> httpx.AsyncClient:
    """
    Returns an HTTPX AsyncClient configured with SSRF validation and
    DNS Rebinding protection.
    """
    validator = validator or SSRFValidator()
    transport = DNSRebindingSafeAsyncTransport(validator=validator)
    
    # We enforce a timeout and limit redirects to prevent redirect-based SSRF bypasses.
    return httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(5.0, connect=2.0),
        follow_redirects=False  # Crucial: Redirects should be handled and validated manually or disabled
    )
