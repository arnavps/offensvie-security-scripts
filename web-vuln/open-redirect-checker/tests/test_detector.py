"""
Automated unit and integration test suite for Open Redirect Detector.
"""
import os
import sys
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

# Dynamic parent path resolution to guarantee out-of-the-box execution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from open_redirect_detector.core.validator import DomainValidator
from open_redirect_detector.core.http_client import AsyncHTTPClient
from open_redirect_detector.core.engine import DetectionEngine
from open_redirect_detector.utils.reporter import Exporter
from open_redirect_detector.modules.param_mutation import ParamMutationChecker
from open_redirect_detector.modules.path_injection import PathInjectionChecker

class TestDomainValidator(unittest.TestCase):
    """
    Tests input normalization and structural domain validation.
    """
    def test_is_valid_url(self):
        self.assertTrue(DomainValidator.is_valid_url("http://example.com"))
        self.assertTrue(DomainValidator.is_valid_url("https://sub.target.org/path"))
        self.assertFalse(DomainValidator.is_valid_url("invalid_domain"))
        self.assertFalse(DomainValidator.is_valid_url("http://"))

    def test_normalize_target(self):
        self.assertEqual(DomainValidator.normalize_target("example.com"), "https://example.com/")
        self.assertEqual(DomainValidator.normalize_target("  http://example.com/  "), "http://example.com/")


class TestAsyncHTTPClient(unittest.IsolatedAsyncioTestCase):
    """
    Tests connection wrappers and HTTP inspection loop flows.
    """
    @patch("aiohttp.ClientSession")
    async def test_session_lifecycle(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.close = AsyncMock()
        mock_session_cls.return_value = mock_session
        
        config = {"http": {"concurrency_limit": 5}}
        
        async with AsyncHTTPClient(config) as client:
            self.assertIsNotNone(client._session)
            
        mock_session.close.assert_called_once()

    @patch("aiohttp.ClientSession")
    async def test_inspect_url_success(self, mock_session_cls):
        mock_response = AsyncMock()
        mock_response.status = 200
        
        class AsyncContextMock:
            async def __aenter__(self):
                return mock_response
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass
                
        mock_session = MagicMock()
        mock_session.closed = False
        mock_session.close = AsyncMock()
        mock_session.request = MagicMock(return_value=AsyncContextMock())
        mock_session_cls.return_value = mock_session
        
        config = {"http": {"concurrency_limit": 5}}
        
        async with AsyncHTTPClient(config) as client:
            res = await client.inspect_url("GET", "https://example.com")
            self.assertEqual(res["status"], 200)
            self.assertIsNone(res["error"])


class TestExporter(unittest.TestCase):
    """
    Tests intelligence JSON report file exports.
    """
    def setUp(self):
        self.temp_file = "temp_report.json"
        
    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
            
    def test_export_json(self):
        data = [{"test": "value"}]
        self.assertTrue(Exporter.export_json(data, self.temp_file))
        self.assertTrue(os.path.exists(self.temp_file))


class TestInspectionModules(unittest.IsolatedAsyncioTestCase):
    """
    Tests parameter mutations and path injection vectors.
    """
    async def test_param_mutation_checker(self):
        config = {
            "payloads": {
                "fuzz_param": "url",
                "targets": ["evil.com"]
            }
        }
        
        checker = ParamMutationChecker("https://target.com/login?url=safe", config)
        
        # Mock client behavior
        mock_client = MagicMock()
        mock_client.inspect_url = AsyncMock(return_value={
            "status": 302,
            "final_destination": "https://evil.com/",
            "redirect_chain": [{"status": 302, "url": "https://target.com/login", "location": "https://evil.com/"}]
        })
        
        findings = await checker.run_checks(mock_client)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["payload"], "evil.com")
        self.assertTrue(findings[0]["is_vulnerable"])

    async def test_path_injection_checker(self):
        config = {
            "payloads": {
                "targets": ["//evil.com"]
            }
        }
        
        checker = PathInjectionChecker("https://target.com", config)
        
        mock_client = MagicMock()
        mock_client.inspect_url = AsyncMock(return_value={
            "status": 302,
            "final_destination": "https://evil.com/",
            "redirect_chain": [{"status": 302, "url": "https://target.com//evil.com", "location": "https://evil.com/"}]
        })
        
        findings = await checker.run_checks(mock_client)
        self.assertEqual(len(findings), 1)
        self.assertTrue(findings[0]["is_vulnerable"])


if __name__ == "__main__":
    unittest.main()
