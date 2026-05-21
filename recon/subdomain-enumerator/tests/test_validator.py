"""
Unit tests for DomainValidator utility functions.
Tests domain syntax correctness, scope enforcement, and input sanitization.
"""

import unittest
from subdomain_collector.utils.validator import DomainValidator

class TestDomainValidator(unittest.TestCase):

    def test_is_valid_domain(self):
        # Valid domains
        self.assertTrue(DomainValidator.is_valid_domain("example.com"))
        self.assertTrue(DomainValidator.is_valid_domain("dev.example.com"))
        self.assertTrue(DomainValidator.is_valid_domain("api.sub.example.co.uk"))
        self.assertTrue(DomainValidator.is_valid_domain("x.org"))
        
        # Invalid domains
        self.assertFalse(DomainValidator.is_valid_domain(""))
        self.assertFalse(DomainValidator.is_valid_domain("example"))
        self.assertFalse(DomainValidator.is_valid_domain("example.com/path"))
        self.assertFalse(DomainValidator.is_valid_domain("example.com?query=1"))
        self.assertFalse(DomainValidator.is_valid_domain("http://example.com"))
        self.assertFalse(DomainValidator.is_valid_domain("user@example.com"))
        self.assertFalse(DomainValidator.is_valid_domain("invalid_char.com"))
        self.assertFalse(DomainValidator.is_valid_domain("a" * 254 + ".com"))

    def test_is_in_scope(self):
        root = "target.com"
        
        # In-scope examples
        self.assertTrue(DomainValidator.is_in_scope("target.com", root))
        self.assertTrue(DomainValidator.is_in_scope("dev.target.com", root))
        self.assertTrue(DomainValidator.is_in_scope("api.staging.target.com", root))
        
        # Out-of-scope examples
        self.assertFalse(DomainValidator.is_in_scope("target.com.attacker.com", root))
        self.assertFalse(DomainValidator.is_in_scope("attacker.com", root))
        self.assertFalse(DomainValidator.is_in_scope("nottarget.com", root))
        self.assertFalse(DomainValidator.is_in_scope("", root))

    def test_sanitize_discovered_name(self):
        self.assertEqual(DomainValidator.sanitize_discovered_name("*.example.com"), "example.com")
        self.assertEqual(DomainValidator.sanitize_discovered_name("  dev.example.com  "), "dev.example.com")
        self.assertEqual(DomainValidator.sanitize_discovered_name("*dev.example.com"), "dev.example.com")
        self.assertEqual(DomainValidator.sanitize_discovered_name("EXAMPLE.com."), "example.com")
        self.assertIsNone(DomainValidator.sanitize_discovered_name("invalid/domain.com"))
        self.assertIsNone(DomainValidator.sanitize_discovered_name(""))

if __name__ == '__main__':
    unittest.main()
