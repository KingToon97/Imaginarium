"""Smoke tests verifying importability and basic app execution."""
import tempfile
import unittest

from imaginarium import Imaginarium
from imaginarium.app import demo
from imaginarium.laws import verify_core_integrity


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_import_imaginarium(self):
        self.assertIsNotNone(Imaginarium)

    def test_app_initializes(self):
        self.assertIsNotNone(self.app.store)
        self.assertIsNotNone(self.app.pipeline)

    def test_demo_callable(self):
        self.assertTrue(callable(demo))

    def test_core_integrity_passes(self):
        verify_core_integrity()

    def test_pipeline_compliant_idea(self):
        idea = {
            "title": "Freelance Invoice Template",
            "description": "An original invoicing template for freelancers.",
            "channel": "local storefront",
            "expected_revenue_pence": 500,
            "expected_cost_pence": 0,
            "vulnerability_risk": "low",
            "legal_confidence": 0.99,
            "customer_value": 0.8,
            "probability_of_sale": 0.2,
            "hours_to_launch": 1.0,
        }
        result = self.app.execute(idea)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "live")

    def test_pipeline_non_compliant_idea(self):
        idea = {
            "title": "Spam Campaign Service",
            "description": "Send bulk spam to email lists.",
            "channel": "email",
            "expected_revenue_pence": 1000,
            "expected_cost_pence": 0,
            "vulnerability_risk": "low",
            "legal_confidence": 0.99,
            "customer_value": 0.8,
            "probability_of_sale": 0.5,
            "hours_to_launch": 1.0,
        }
        result = self.app.execute(idea)
        self.assertEqual(result["status"], "rejected_by_GLaDOS")


if __name__ == "__main__":
    unittest.main()
