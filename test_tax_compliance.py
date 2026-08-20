"""Tests for the HMRC Tax Compliance module."""
from __future__ import annotations

import os
import tempfile
import unittest
import unittest.mock as mock

from imaginarium.app import Imaginarium
from imaginarium.tax_compliance import (
    BASIC_RATE_UPPER_PENCE,
    PERSONAL_ALLOWANCE_PENCE,
    TRADING_ALLOWANCE_PENCE,
    VAT_THRESHOLD_PENCE,
    TaxCompliance,
)


class TaxComplianceBaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Imaginarium(self.tmp.name)
        self.tax = self.app.tax

    def tearDown(self):
        self.tmp.cleanup()

    def _book_revenue(self, pence: int):
        self.app.store.book_revenue(pence, "test sale")


class TestTradingAllowancePhase1(TaxComplianceBaseTest):
    """Phase 1: £0–£1,000 — tax-free trading allowance."""

    def test_zero_revenue_is_phase_1(self):
        result = self.tax.trading_allowance_status()
        self.assertEqual(result["phase"], 1)
        self.assertFalse(result["trading_allowance_exceeded"])
        self.assertEqual(result["gross_revenue_pence"], 0)
        self.assertEqual(result["alerts"], [])

    def test_below_threshold_no_filing_required(self):
        self._book_revenue(50_000)  # £500
        result = self.tax.trading_allowance_status()
        self.assertEqual(result["phase"], 1)
        self.assertFalse(result["trading_allowance_exceeded"])
        self.assertEqual(result["alerts"], [])

    def test_exactly_at_threshold_no_filing(self):
        self._book_revenue(TRADING_ALLOWANCE_PENCE)  # exactly £1,000
        result = self.tax.trading_allowance_status()
        self.assertFalse(result["trading_allowance_exceeded"])
        self.assertEqual(result["phase"], 1)

    def test_remaining_allowance_calculated_correctly(self):
        self._book_revenue(30_000)  # £300
        result = self.tax.trading_allowance_status()
        self.assertEqual(result["trading_allowance_remaining_pence"], 70_000)  # £700


class TestSelfAssessmentThreshold(TaxComplianceBaseTest):
    """Phase 2: crossing £1,000 triggers Self Assessment."""

    def test_crossing_1000_triggers_alert(self):
        self._book_revenue(100_001)  # £1,000.01
        result = self.tax.trading_allowance_status()
        self.assertTrue(result["trading_allowance_exceeded"])
        self.assertEqual(result["phase"], 2)
        self.assertTrue(any("Self Assessment" in a for a in result["alerts"]))

    def test_self_assessment_forecast_filing_required(self):
        self._book_revenue(200_000)  # £2,000
        forecast = self.tax.self_assessment_forecast()
        self.assertTrue(forecast["filing_required"])
        self.assertIsNotNone(forecast["registration_deadline"])
        self.assertIsNotNone(forecast["payment_deadline"])

    def test_registration_deadline_is_5_october(self):
        self._book_revenue(200_000)
        forecast = self.tax.self_assessment_forecast()
        deadline = forecast["registration_deadline"]
        self.assertIn("-10-05", deadline)

    def test_payment_deadline_is_31_january(self):
        self._book_revenue(200_000)
        forecast = self.tax.self_assessment_forecast()
        deadline = forecast["payment_deadline"]
        self.assertIn("-01-31", deadline)

    def test_below_personal_allowance_no_tax_due(self):
        self._book_revenue(500_000)  # £5,000 — above trading allowance, below personal allowance
        forecast = self.tax.self_assessment_forecast()
        # Profit after £1,000 allowance = £4,000 — still below personal allowance (£12,570)
        self.assertEqual(forecast["income_tax_pence"], 0)
        self.assertEqual(forecast["total_ni_pence"], 0)


class TestExpenseCalculation(TaxComplianceBaseTest):
    """Allowance vs. itemised expenses comparison."""

    def _log_expense(self, amount_pence: int, category: str = "software"):
        return self.tax.log_expense(
            date_str="2024-06-01",
            category=category,
            amount_pence=amount_pence,
            description="Test expense",
            receipt_ref="RCPT-001",
            justification="Legitimate business software subscription",
        )

    def test_trading_allowance_preferred_when_expenses_low(self):
        self._book_revenue(500_000)  # £5,000
        self._log_expense(50_000)    # £500 in expenses — less than £1,000 allowance
        result = self.tax.allowable_expenses_vs_allowance()
        self.assertEqual(result["recommendation"], "trading_allowance")

    def test_itemised_preferred_when_expenses_exceed_allowance(self):
        self._book_revenue(2_000_000)   # £20,000 — above personal allowance so tax applies
        self._log_expense(200_000)      # £2,000 in expenses — more than £1,000 allowance
        result = self.tax.allowable_expenses_vs_allowance()
        self.assertEqual(result["recommendation"], "itemised_expenses")

    def test_k2so_rejects_invalid_category(self):
        result = self.tax.log_expense(
            date_str="2024-06-01",
            category="personal_holiday",
            amount_pence=10_000,
            description="Holiday",
            receipt_ref="RCPT-002",
            justification="Not business related",
        )
        self.assertFalse(result["approved"])

    def test_k2so_rejects_missing_receipt(self):
        result = self.tax.log_expense(
            date_str="2024-06-01",
            category="software",
            amount_pence=10_000,
            description="Software",
            receipt_ref="",
            justification="Business software",
        )
        self.assertFalse(result["approved"])

    def test_k2so_rejects_missing_justification(self):
        result = self.tax.log_expense(
            date_str="2024-06-01",
            category="software",
            amount_pence=10_000,
            description="Software",
            receipt_ref="RCPT-003",
            justification="",
        )
        self.assertFalse(result["approved"])

    def test_k2so_approves_valid_expense(self):
        result = self._log_expense(10_000)
        self.assertTrue(result["approved"])
        self.assertEqual(result["approved_by"], "K-2SO")
        self.assertIsNotNone(result["expense_id"])

    def test_expense_appears_in_tracker(self):
        self._log_expense(10_000)
        tracker = self.tax.expenses_tracker()
        self.assertEqual(tracker["total_approved_expenses_pence"], 10_000)
        self.assertEqual(tracker["expense_count"], 1)


class TestPensionContributionTaxRelief(TaxComplianceBaseTest):
    """Pension contribution opportunity calculation."""

    def test_zero_revenue_zero_relief(self):
        result = self.tax.pension_contribution_opportunity(100_000)
        self.assertEqual(result["income_tax_relief_pence"], 0)

    def test_basic_rate_relief_above_personal_allowance(self):
        self._book_revenue(3_000_000)  # £30,000 — above personal allowance
        result = self.tax.pension_contribution_opportunity(100_000)  # £1,000 pension
        # Marginal rate should be 20% basic rate
        self.assertAlmostEqual(result["marginal_income_tax_rate_pct"], 20.0)
        self.assertEqual(result["income_tax_relief_pence"], 20_000)

    def test_net_cost_is_contribution_minus_relief(self):
        self._book_revenue(3_000_000)  # £30,000
        result = self.tax.pension_contribution_opportunity(100_000)
        self.assertEqual(
            result["net_cost_pence"],
            result["contribution_pence"] - result["total_relief_pence"],
        )

    def test_negative_contribution_raises_error(self):
        with self.assertRaises(ValueError):
            self.tax.pension_contribution_opportunity(-100)


class TestVATThresholdForecast(TaxComplianceBaseTest):
    """VAT threshold tracking and Flat Rate Scheme eligibility."""

    def test_zero_revenue_not_mandatory(self):
        result = self.tax.vat_threshold_forecast()
        self.assertFalse(result["vat_registration_mandatory"])
        self.assertEqual(result["threshold_pct_used"], 0.0)

    def test_below_threshold_not_mandatory(self):
        self._book_revenue(VAT_THRESHOLD_PENCE - 1)
        result = self.tax.vat_threshold_forecast()
        self.assertFalse(result["vat_registration_mandatory"])

    def test_at_or_above_threshold_mandatory(self):
        self._book_revenue(VAT_THRESHOLD_PENCE)
        result = self.tax.vat_threshold_forecast()
        self.assertTrue(result["vat_registration_mandatory"])

    def test_flat_rate_scheme_eligible_below_150k(self):
        self._book_revenue(VAT_THRESHOLD_PENCE)
        result = self.tax.vat_threshold_forecast()
        self.assertTrue(result["flat_rate_scheme_eligible"])

    def test_remaining_to_threshold_decreases(self):
        self._book_revenue(4_500_000)  # £45,000
        result = self.tax.vat_threshold_forecast()
        self.assertEqual(result["remaining_to_threshold_pence"], VAT_THRESHOLD_PENCE - 4_500_000)
        self.assertAlmostEqual(result["threshold_pct_used"], 50.0)


class TestIncorporationAnalysis(TaxComplianceBaseTest):
    """Limited company incorporation analysis at £50k+ profit."""

    def test_below_50k_does_not_recommend_incorporation(self):
        self._book_revenue(3_000_000)  # £30,000
        result = self.tax.incorporation_analysis()
        self.assertFalse(result["recommend_incorporation"])

    def test_above_50k_may_recommend_incorporation(self):
        self._book_revenue(BASIC_RATE_UPPER_PENCE + 1_000_000)  # £60,270
        result = self.tax.incorporation_analysis()
        # Incorporation may be recommended — just check the analysis runs and has data
        self.assertIn("sole_trader_total_tax_ni_pence", result)
        self.assertIn("limited_company_total_tax_pence", result)
        self.assertIn("recommend_incorporation", result)

    def test_analysis_contains_required_fields(self):
        self._book_revenue(6_000_000)
        result = self.tax.incorporation_analysis()
        required = [
            "taxable_profit_pence", "sole_trader_total_tax_ni_pence",
            "limited_company_total_tax_pence", "recommend_incorporation",
            "estimated_annual_saving_pence", "note",
        ]
        for field in required:
            self.assertIn(field, result)


class TestTaxYearSummary(TaxComplianceBaseTest):
    """Tax year summary produces correct consolidated output."""

    def test_summary_contains_all_required_fields(self):
        self._book_revenue(200_000)  # £2,000
        summary = self.tax.tax_year_summary()
        required = [
            "tax_year", "gross_revenue_pence", "gross_revenue_gbp",
            "itemised_expenses_pence", "deduction_recommended",
            "deduction_applied_pence", "taxable_profit_pence",
            "personal_allowance_pence", "income_tax_due_pence",
            "total_tax_and_ni_pence", "effective_tax_rate_pct",
            "filing_required", "registration_deadline", "payment_deadline",
        ]
        for field in required:
            self.assertIn(field, summary)

    def test_effective_rate_zero_within_allowance(self):
        self._book_revenue(50_000)  # £500 — within trading allowance
        summary = self.tax.tax_year_summary()
        self.assertEqual(summary["total_tax_and_ni_pence"], 0)


class TestTaxServerEndpoints(unittest.TestCase):
    """Verify the FastAPI tax compliance endpoints respond correctly."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._env_patch = mock.patch.dict(os.environ, {"IMAGINARIUM_HOME": self.tmp.name})
        self._env_patch.start()

        from fastapi.testclient import TestClient
        from imaginarium.server import server

        self._client_ctx = TestClient(server)
        self.client = self._client_ctx.__enter__()

    def tearDown(self):
        self._client_ctx.__exit__(None, None, None)
        self._env_patch.stop()
        self.tmp.cleanup()

    def test_tax_status_endpoint(self):
        r = self.client.get("/tax-status")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("phase", data)
        self.assertIn("gross_revenue_pence", data)
        self.assertIn("trading_allowance_exceeded", data)

    def test_tax_forecast_endpoint(self):
        r = self.client.get("/tax-compliance/forecast")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("filing_required", data)
        self.assertIn("total_tax_and_ni_pence", data)

    def test_tax_expenses_endpoint(self):
        r = self.client.get("/tax-compliance/expenses")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("total_approved_expenses_pence", data)

    def test_log_expense_valid(self):
        payload = {
            "date": "2024-06-01",
            "category": "software",
            "amount_pence": 1500,
            "description": "Canva subscription",
            "receipt_ref": "RCPT-CANVA-001",
            "justification": "Design tool for digital product creation",
        }
        r = self.client.post("/tax-compliance/log-expense", json=payload)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json()["approved"])

    def test_log_expense_invalid_category(self):
        payload = {
            "date": "2024-06-01",
            "category": "personal_shopping",
            "amount_pence": 1500,
            "description": "Shopping",
            "receipt_ref": "RCPT-001",
            "justification": "Personal",
        }
        r = self.client.post("/tax-compliance/log-expense", json=payload)
        self.assertEqual(r.status_code, 400)
        self.assertFalse(r.json()["approved"])

    def test_tax_efficiency_endpoint(self):
        r = self.client.get("/tax-compliance/efficiency")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("recommendations", data)
        self.assertIsInstance(data["recommendations"], list)

    def test_vat_forecast_endpoint(self):
        r = self.client.get("/tax-compliance/vat-forecast")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("vat_registration_mandatory", data)
        self.assertIn("flat_rate_scheme_eligible", data)

    def test_audit_trail_endpoint(self):
        r = self.client.get("/tax-compliance/audit-trail")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn("audit_trail", data)
        self.assertIn("count", data)


if __name__ == "__main__":
    unittest.main()
