"""Smoke tests verifying importability and basic app execution."""
from datetime import datetime, timedelta, timezone
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
        from imaginarium.server import _get_app, server

        # Enter client context so lifespan runs for the duration of each test
        self._client_ctx = TestClient(server)
        self.client = self._client_ctx.__enter__()
        self.runtime = _get_app()

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

    def test_dashboard_endpoints(self):
        payload = {
            "title": "Revenue Dashboard Template",
            "description": "An original dashboard template for finance tracking.",
            "channel": "local storefront",
            "expected_revenue_pence": 1_500,
            "expected_cost_pence": 0,
            "vulnerability_risk": "low",
            "legal_confidence": 0.99,
            "customer_value": 0.9,
            "probability_of_sale": 0.25,
            "hours_to_launch": 1.0,
        }
        created = self.client.post("/execute", json=payload)
        self.assertEqual(created.status_code, 200)
        proposal_id = created.json()["proposal"]
        now = datetime.now(timezone.utc)
        last_month = now - timedelta(days=32)
        self.runtime.store.record_sale(proposal_id, gross_pence=1_500, fee_pence=150)
        self.runtime.store.record_sale(proposal_id, gross_pence=1_000, fee_pence=100, ts=last_month)
        self.runtime.store.book_expense(200, "Approved marketing spend")

        summary = self.client.get("/api/v1/revenue/summary")
        self.assertEqual(summary.status_code, 200)
        summary_data = summary.json()
        self.assertEqual(summary_data["current_balance_pence"], 2_050)
        self.assertEqual(summary_data["revenue"]["today_net_pence"], 1_350)
        self.assertEqual(summary_data["tax"]["deduction_strategy"], "trading_allowance")
        self.assertTrue(summary_data["milestones"])

        products = self.client.get("/api/v1/revenue/products")
        self.assertEqual(products.status_code, 200)
        product_data = products.json()["products"][0]
        self.assertEqual(product_data["product_name"], "Revenue Dashboard Template")
        self.assertEqual(product_data["sales_count_all_time"], 2)

        forecast = self.client.get("/api/v1/revenue/forecast")
        self.assertEqual(forecast.status_code, 200)
        self.assertIn("projections", forecast.json())

        agents = self.client.get("/api/v1/agents/roster")
        self.assertEqual(agents.status_code, 200)
        agents_data = agents.json()
        self.assertIn("agents", agents_data)
        self.assertIn("morale_trend", agents_data)

        activity = self.client.get("/api/v1/activity/feed", params={"event_type": "sales"})
        self.assertEqual(activity.status_code, 200)
        self.assertTrue(activity.json()["items"])


if __name__ == "__main__":
    unittest.main()
