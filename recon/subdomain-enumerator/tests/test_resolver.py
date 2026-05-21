"""
Unit tests for the AsyncDNSResolver class using mock DNS queries.
Verifies resolution formats, NXDOMAIN error handling, and wildcard comparative filters.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import dns.resolver

from subdomain_collector.core.resolver import AsyncDNSResolver

class TestAsyncDNSResolver(unittest.TestCase):

    def setUp(self):
        self.config = {
            "dns": {
                "resolvers": ["1.1.1.1"],
                "concurrency_limit": 5,
                "timeout": 1.0
            }
        }
        self.resolver = AsyncDNSResolver(self.config)

    @patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock)
    def test_resolve_single_success(self, mock_resolve):
        # Mock successful resolution returning IP A records
        mock_answer = MagicMock()
        mock_answer.to_text.return_value = "93.184.216.34"
        mock_resolve.return_value = [mock_answer]
        
        res = asyncio.run(self.resolver._resolve_single("dev.example.com"))
        
        self.assertEqual(res["status"], "Active")
        self.assertIn("93.184.216.34", res["ips"])
        self.assertEqual(res["subdomain"], "dev.example.com")

    @patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock)
    def test_resolve_single_nxdomain(self, mock_resolve):
        # Mock NXDOMAIN exception
        mock_resolve.side_effect = dns.resolver.NXDOMAIN()
        
        res = asyncio.run(self.resolver._resolve_single("dead.example.com"))
        
        self.assertEqual(res["status"], "Inactive")
        self.assertEqual(res["ips"], [])

    @patch("dns.asyncresolver.Resolver.resolve", new_callable=AsyncMock)
    def test_resolve_single_wildcard_polluted(self, mock_resolve):
        # First, mock wildcard check detection
        mock_answer_wc = MagicMock()
        mock_answer_wc.to_text.return_value = "127.0.0.1"
        mock_resolve.return_value = [mock_answer_wc]
        
        asyncio.run(self.resolver.detect_wildcard("example.com"))
        
        self.assertTrue(self.resolver.wildcard_detected)
        self.assertIn("127.0.0.1", self.resolver.wildcard_ips)
        
        # Resolve a polluted domain
        res = asyncio.run(self.resolver._resolve_single("polluted.example.com"))
        self.assertEqual(res["status"], "WildcardPolluted")
        self.assertEqual(res["ips"], ["127.0.0.1"])

if __name__ == '__main__':
    unittest.main()
