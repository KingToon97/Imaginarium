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


class ServerSmokeTests(unittest.TestCase):
    """Verify the FastAPI server routes respond correctly."""

    def setUp(self):
        import os
        import unittest.mock as mock

        self.tmp = tempfile.TemporaryDirectory()
        self._env_patch = mock.patch.dict(os.environ, {"IMAGINARIUM_HOME": self.tmp.name})
        self._env_patch.start()

        from fastapi.testclient import TestClient
        from imaginarium.server import server

        # Enter client context so lifespan runs for the duration of each test
        self._client_ctx = TestClient(server)
        self.client = self._client_ctx.__enter__()

    def tearDown(self):
        self._client_ctx.__exit__(None, None, None)
        self._env_patch.stop()
        self.tmp.cleanup()

    def test_healthz(self):
        r = self.client.get("/healthz")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(), {"status": "ok"})

    def test_status(self):
        r = self.client.get("/status")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("balance_pence", data)
        self.assertIn("agents", data)

    def test_execute_compliant(self):
        payload = {
            "title": "Budget Template",
            "description": "An original budgeting template for freelancers.",
            "channel": "local storefront",
            "expected_revenue_pence": 500,
            "expected_cost_pence": 0,
            "vulnerability_risk": "low",
            "legal_confidence": 0.99,
            "customer_value": 0.8,
            "probability_of_sale": 0.2,
            "hours_to_launch": 1.0,
        }
        r = self.client.post("/execute", json=payload)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "live")


if __name__ == "__main__":
    unittest.main()
