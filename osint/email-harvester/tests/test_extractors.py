import unittest
from harvester.utils.extractors import EmailExtractor

class TestEmailExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = EmailExtractor("example.com")

    def test_extract_valid_emails(self):
        text = "Contact us at info@example.com or support@example.com."
        results = self.extractor.extract(text)
        self.assertEqual(results, {"info@example.com", "support@example.com"})

    def test_extract_obfuscated_emails(self):
        text = "Email admin[at]example.com or admin (at) example.com"
        results = self.extractor.extract(text)
        self.assertEqual(results, {"admin@example.com"})

    def test_reject_false_positives(self):
        # image.png@example.com is technically valid according to simple regex, 
        # but our heuristic should reject it.
        text = "We found image.png@example.com and background.css@example.com"
        results = self.extractor.extract(text)
        self.assertEqual(results, set())

    def test_subdomains(self):
        text = "Email sales@uk.example.com"
        results = self.extractor.extract(text)
        self.assertEqual(results, {"sales@uk.example.com"})

if __name__ == '__main__':
    unittest.main()
