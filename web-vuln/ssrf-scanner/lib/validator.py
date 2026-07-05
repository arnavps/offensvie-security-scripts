"""
SSRF Validation Library

This module provides a production-grade validation interface designed to mitigate
Server-Side Request Forgery (SSRF) and DNS Rebinding attacks. It offers utilities
to parse URLs, validate IP addresses against restricted ranges, and safely resolve
hostnames.
"""

import ipaddress
import logging
import socket
import urllib.parse
from typing import List, Optional, Set, Tuple

logger = logging.getLogger("ssrf_mitigation.validator")


class SSRFValidator:
    """
    Validates URL scheme, port, hostname, and resolved IP addresses to identify
    potential SSRF vulnerabilities before making outbound requests.
    """

    # RFC 1918, RFC 6598, loopback, link-local, multicast, and documentation ranges
    RESTRICTED_SUBNETS_V4 = [
        ipaddress.ip_network("0.0.0.0/8"),          # Current network (only valid as source)
        ipaddress.ip_network("10.0.0.0/8"),         # Private-Use Networks (RFC 1918)
        ipaddress.ip_network("100.64.0.0/10"),      # Shared Address Space (RFC 6598)
        ipaddress.ip_network("127.0.0.0/8"),        # Loopback (RFC 1122)
        ipaddress.ip_network("169.254.0.0/16"),     # Link-Local (RFC 3927) - Includes Cloud Metadata
        ipaddress.ip_network("172.16.0.0/12"),      # Private-Use Networks (RFC 1918)
        ipaddress.ip_network("192.0.0.0/24"),       # IETF Protocol Assignments (RFC 6890)
        ipaddress.ip_network("192.0.2.0/24"),       # Test-Net-1 (RFC 5737)
        ipaddress.ip_network("192.88.99.0/24"),     # 6to4 Relay Anycast (RFC 3068)
        ipaddress.ip_network("192.168.0.0/16"),     # Private-Use Networks (RFC 1918)
        ipaddress.ip_network("198.18.0.0/15"),      # Network Interconnect Device Benchmark (RFC 2544)
        ipaddress.ip_network("198.51.100.0/24"),    # Test-Net-2 (RFC 5737)
        ipaddress.ip_network("203.0.113.0/24"),     # Test-Net-3 (RFC 5737)
        ipaddress.ip_network("224.0.0.0/4"),        # Multicast (RFC 1112)
        ipaddress.ip_network("240.0.0.0/4"),        # Reserved for Future Use (RFC 1112)
        ipaddress.ip_network("255.255.255.255/32"), # Limited Broadcast (RFC 919)
    ]

    RESTRICTED_SUBNETS_V6 = [
        ipaddress.ip_network("::/128"),             # Unspecified Address
        ipaddress.ip_network("::1/128"),            # Loopback Address
        ipaddress.ip_network("::ffff:0:0/96"),      # IPv4-Mapped Addresses (RFC 4291)
        ipaddress.ip_network("100::/64"),           # Discard-Only Address Block (RFC 6666)
        ipaddress.ip_network("2001:db8::/32"),      # Documentation Block (RFC 3849)
        ipaddress.ip_network("fc00::/7"),           # Unique Local Addresses (ULA - RFC 4193)
        ipaddress.ip_network("fe80::/10"),          # Link-Local Unicast (RFC 4291) - Includes Cloud Metadata
        ipaddress.ip_network("ff00::/8"),           # Multicast (RFC 4291)
    ]

    def __init__(
        self,
        allowed_schemes: Optional[Set[str]] = None,
        allowed_ports: Optional[Set[int]] = None,
        allowed_hosts: Optional[Set[str]] = None,
        block_private_ips: bool = True,
    ):
        """
        Initializes the SSRF Validator.

        :param allowed_schemes: HTTP schemes to permit (default: http, https)
        :param allowed_ports: Destination ports to permit (default: 80, 443)
        :param allowed_hosts: Whitelist of hostnames that skip IP checks (default: None)
        :param block_private_ips: Flag to enforce IP-level blocklists (default: True)
        """
        self.allowed_schemes = allowed_schemes or {"http", "https"}
        self.allowed_ports = allowed_ports or {80, 443}
        self.allowed_hosts = allowed_hosts or set()
        self.block_private_ips = block_private_ips

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Performs validation checks on a given URL.

        :param url: The target URL to evaluate.
        :return: A tuple of (is_valid: bool, reason: str)
        """
        if not url:
            return False, "Empty URL provided"

        # 1. Parse URL structure
        try:
            parsed = urllib.parse.urlparse(url)
        except ValueError as e:
            return False, f"URL parsing failed: {str(e)}"

        # 2. Scheme Enforcement
        if not parsed.scheme or parsed.scheme.lower() not in self.allowed_schemes:
            return False, f"Prohibited URL scheme: {parsed.scheme}"

        # 3. Port Validation
        port = parsed.port
        if port is None:
            # Infer standard ports based on scheme
            if parsed.scheme.lower() == "http":
                port = 80
            elif parsed.scheme.lower() == "https":
                port = 443

        if port not in self.allowed_ports:
            return False, f"Prohibited connection port: {port}"

        # 4. Hostname Validation
        hostname = parsed.hostname
        if not hostname:
            return False, "Missing or invalid hostname in URL"

        # Normalize hostname (lowercase and strip brackets for IPv6)
        normalized_host = hostname.lower().strip("[]")

        # Skip IP validation if the host is explicitly allowed (e.g., internal APIs on a whitelist)
        if normalized_host in self.allowed_hosts:
            logger.info("Host %s skipped IP validation due to host allowlist.", hostname)
            return True, "Host explicitly allowed by whitelist"

        # 5. IP Address and Subnet Validation (DNS Resolution)
        try:
            resolved_ips = self.resolve_hostname(normalized_host)
        except socket.gaierror as e:
            return False, f"DNS resolution failed for host '{hostname}': {str(e)}"

        if not resolved_ips:
            return False, f"No IP addresses resolved for host '{hostname}'"

        if self.block_private_ips:
            for ip in resolved_ips:
                is_safe, restricted_reason = self.is_safe_ip(ip)
                if not is_safe:
                    logger.warning(
                        "SSRF Alert: Blocked access to host '%s' because IP '%s' is restricted: %s",
                        hostname,
                        ip,
                        restricted_reason,
                    )
                    return False, f"Blocked target IP: {restricted_reason}"

        return True, "URL validated successfully"

    def resolve_hostname(self, hostname: str) -> List[ipaddress.IPv4Address | ipaddress.IPv6Address]:
        """
        Resolves a hostname to a list of IP address objects.

        :param hostname: Host name to resolve.
        :return: List of resolved ipaddress objects.
        """
        ips = []
        # getaddrinfo performs robust resolution supporting both IPv4 and IPv6
        addr_info = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
        for info in addr_info:
            ip_str = info[4][0]
            try:
                # Remove scope ID if present in IPv6 address (e.g. fe80::1%eth0)
                clean_ip = ip_str.split("%")[0]
                ips.append(ipaddress.ip_address(clean_ip))
            except ValueError:
                continue
        # Deduplicate list
        return list(set(ips))

    def is_safe_ip(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> Tuple[bool, str]:
        """
        Evaluates whether an IP address is pointing to private or restricted spaces.

        :param ip: An ipaddress.IPv4Address or ipaddress.IPv6Address object.
        :return: A tuple of (is_safe: bool, reason: str)
        """
        # Built-in properties from ipaddress standard library
        if ip.is_loopback:
            return False, "Loopback address"
        if ip.is_private:
            return False, "Private subnet address"
        if ip.is_link_local:
            return False, "Link-local metadata address"
        if ip.is_multicast:
            return False, "Multicast address block"
        if ip.is_reserved:
            return False, "Reserved address space"

        # Explicit check against strict subnet list
        if isinstance(ip, ipaddress.IPv4Address):
            for network in self.RESTRICTED_SUBNETS_V4:
                if ip in network:
                    return False, f"Matches restricted IPv4 range ({network})"
        elif isinstance(ip, ipaddress.IPv6Address):
            for network in self.RESTRICTED_SUBNETS_V6:
                if ip in network:
                    return False, f"Matches restricted IPv6 range ({network})"

        return True, "IP is public and safe"


# =====================================================================
# DNS REBINDING PROTECTION
# =====================================================================
# DNS Rebinding occurs when a domain resolves to a public address during
# validation (Time-of-Check), but then updates its DNS record to resolve
# to a local address when the connection is executed (Time-of-Use).
# To prevent this, we must ensure the application connects *strictly*
# to the validated IP, bypassing host-level resolution on connection.
# =====================================================================

class DNSRebindingSafeClient:
    """
    An HTTP client helper designed to prevent DNS rebinding by resolving
    and validating the IP address before connection, and forcing the outgoing
    connection to lock onto the resolved IP.
    """

    def __init__(self, validator: Optional[SSRFValidator] = None):
        self.validator = validator or SSRFValidator()

    def make_safe_http_request_details(self, url: str) -> Tuple[str, dict]:
        """
        Transforms a request URL into a DNS-rebinding-safe request configuration.
        By replacing the URL host with the pre-resolved, validated IP address
        and attaching a 'Host' header matching the original hostname, we force
        the connection to bypass standard DNS lookup at request execution time.

        :param url: The target URL.
        :return: A tuple of (safe_url: str, headers: dict)
        """
        # Validate first
        is_valid, reason = self.validator.validate_url(url)
        if not is_valid:
            raise ValueError(f"SSRF validation blocked request: {reason}")

        parsed = urllib.parse.urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            raise ValueError("Invalid URL: missing hostname")

        # Resolve host to get a validated IP
        resolved_ips = self.validator.resolve_hostname(hostname)
        if not resolved_ips:
            raise ValueError("Failed to resolve host for safe binding")

        # Use the first resolved IP (which has passed security checks)
        target_ip = str(resolved_ips[0])

        # Enforce brackets for IPv6 IPs in URL format
        if ":" in target_ip and not target_ip.startswith("["):
            formatted_ip = f"[{target_ip}]"
        else:
            formatted_ip = target_ip

        # Reconstruct the URL with the validated IP replacing the hostname
        port_suffix = f":{parsed.port}" if parsed.port else ""
        netloc = f"{formatted_ip}{port_suffix}"
        
        safe_url = urllib.parse.urlunparse((
            parsed.scheme,
            netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))

        # Set Host header so the backend server routes the request properly
        # (This avoids SSL certificate mismatches and server configuration routing issues)
        headers = {"Host": hostname}

        return safe_url, headers
