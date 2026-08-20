"""HMRC Tax Compliance Module for Imaginarium.

Implements HMRC-compliant tax tracking, forecasting, and efficiency analysis
for a UK sole trader starting from £0 revenue.

All strategies used are legitimate HMRC-approved reliefs only:
  - Trading allowance (£1,000 gross revenue)
  - Personal allowance (£12,570)
  - Pension contributions relief
  - Annual Investment Allowance
  - Actual/itemised allowable expenses
  - VAT Flat Rate Scheme (where eligible)

No aggressive or artificial tax avoidance schemes are implemented.
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timezone
from typing import Any

from .store import Store

# ---------------------------------------------------------------------------
# HMRC thresholds (2024/25 tax year) — update annually
# ---------------------------------------------------------------------------

TRADING_ALLOWANCE_PENCE = 100_000        # £1,000
PERSONAL_ALLOWANCE_PENCE = 1_257_000     # £12,570
BASIC_RATE_UPPER_PENCE = 5_027_000       # £50,270
BASIC_RATE = 0.20
CLASS_2_NI_ANNUAL_PENCE = 16_380         # £163.80/year
CLASS_4_NI_RATE = 0.08                   # 8% on profit between £12,570–£50,270
VAT_THRESHOLD_PENCE = 9_000_000          # £90,000
VAT_FLAT_RATE = 0.165                    # 16.5%
CORP_TAX_RATE = 0.19                     # 19% small profits rate (2024/25)
DIVIDEND_ALLOWANCE_PENCE = 50_000        # £500/year tax-free dividend allowance

ALLOWABLE_CATEGORIES = {
    "home_office",
    "software",
    "hosting",
    "domain",
    "marketing",
    "professional_dev",
    "equipment",
}


def _pence_to_gbp(pence: int) -> str:
    return f"£{pence / 100:.2f}"


def _tax_year_start() -> date:
    """Return the start of the current or configured tax year (default 6 April 2024)."""
    raw = os.getenv("IMAGINARIUM_TAX_YEAR_START", "2024-04-06")
    return date.fromisoformat(raw)


def _tax_year_end(start: date) -> date:
    return date(start.year + 1, 4, 5)


def _self_assessment_registration_deadline(tax_year_start: date) -> date:
    """5 October after the tax year ends."""
    return date(tax_year_start.year + 1, 10, 5)


def _self_assessment_payment_deadline(tax_year_start: date) -> date:
    """31 January after the tax year ends."""
    return date(tax_year_start.year + 2, 1, 31)


# ---------------------------------------------------------------------------
# TaxCompliance class
# ---------------------------------------------------------------------------


class TaxCompliance:
    """K-2SO-authorised HMRC tax compliance and efficiency engine."""

    def __init__(self, store: Store):
        self.store = store

    # ------------------------------------------------------------------
    # Core revenue and profit helpers
    # ------------------------------------------------------------------

    def _gross_revenue_pence(self) -> int:
        return self.store.gross_revenue()

    def _total_approved_expenses_pence(self) -> int:
        return self.store.total_approved_expenses_pence()

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def trading_allowance_status(self) -> dict[str, Any]:
        """Current gross revenue vs. £1,000 trading allowance threshold."""
        gross = self._gross_revenue_pence()
        remaining = max(0, TRADING_ALLOWANCE_PENCE - gross)
        exceeded = gross > TRADING_ALLOWANCE_PENCE

        if gross <= TRADING_ALLOWANCE_PENCE:
            phase = 1
            tax_position = "Tax-free: gross revenue within £1,000 trading allowance. No filing required."
        elif gross <= PERSONAL_ALLOWANCE_PENCE:
            phase = 2
            tax_position = (
                "Self Assessment required. Revenue exceeds trading allowance but within "
                "personal allowance (£12,570). Tax likely £0 after deductions."
            )
        elif gross <= BASIC_RATE_UPPER_PENCE:
            phase = 3
            tax_position = (
                "Basic rate income tax (20%) applies on profit above £12,570. "
                "Class 2 NI and Class 4 NI also due."
            )
        else:
            phase = 4
            tax_position = (
                "Higher rate tax applies. Consider limited company incorporation analysis."
            )

        alerts = []
        if gross > TRADING_ALLOWANCE_PENCE:
            ty_start = _tax_year_start()
            reg_deadline = _self_assessment_registration_deadline(ty_start)
            alerts.append(
                f"Self Assessment registration required by {reg_deadline.isoformat()} "
                "(5 Oct after tax year ends)."
            )
        if gross > PERSONAL_ALLOWANCE_PENCE:
            alerts.append(
                "Revenue exceeds personal allowance (£12,570). "
                "Consider pension contributions to reduce taxable profit."
            )
        if gross > BASIC_RATE_UPPER_PENCE:
            alerts.append(
                "Revenue exceeds £50,270. Consider limited company incorporation analysis."
            )
        if gross > VAT_THRESHOLD_PENCE:
            alerts.append(
                "Revenue exceeds £90,000. VAT registration mandatory; "
                "VAT Flat Rate Scheme available."
            )

        return {
            "gross_revenue_pence": gross,
            "gross_revenue_gbp": _pence_to_gbp(gross),
            "trading_allowance_pence": TRADING_ALLOWANCE_PENCE,
            "trading_allowance_remaining_pence": remaining,
            "trading_allowance_remaining_gbp": _pence_to_gbp(remaining),
            "trading_allowance_exceeded": exceeded,
            "phase": phase,
            "tax_position": tax_position,
            "alerts": alerts,
        }

    def allowable_expenses_vs_allowance(self) -> dict[str, Any]:
        """Compare £1,000 trading allowance vs. itemised actual expenses; recommend the better option."""
        itemised_pence = self._total_approved_expenses_pence()
        gross = self._gross_revenue_pence()

        if gross <= TRADING_ALLOWANCE_PENCE:
            return {
                "recommendation": "trading_allowance",
                "reason": "Gross revenue ≤ £1,000 — use trading allowance; no filing or expense tracking required.",
                "trading_allowance_pence": TRADING_ALLOWANCE_PENCE,
                "itemised_expenses_pence": itemised_pence,
                "tax_saving_trading_allowance_pence": 0,
                "tax_saving_itemised_pence": 0,
                "additional_saving_pence": 0,
            }

        # Calculate taxable profit under each option
        profit_with_allowance = max(0, gross - TRADING_ALLOWANCE_PENCE)
        profit_with_itemised = max(0, gross - itemised_pence)

        # Tax due under each (simplified: 20% basic rate for demonstration)
        def _tax_on_profit(profit: int) -> int:
            taxable = max(0, profit - PERSONAL_ALLOWANCE_PENCE)
            return int(taxable * BASIC_RATE)

        tax_allowance = _tax_on_profit(profit_with_allowance)
        tax_itemised = _tax_on_profit(profit_with_itemised)

        if tax_allowance <= tax_itemised:
            recommendation = "trading_allowance"
            reason = (
                f"Trading allowance (£1,000) saves more tax than itemised expenses "
                f"({_pence_to_gbp(itemised_pence)}). "
                f"Tax under allowance: {_pence_to_gbp(tax_allowance)} vs "
                f"itemised: {_pence_to_gbp(tax_itemised)}."
            )
            additional_saving = tax_itemised - tax_allowance
        else:
            recommendation = "itemised_expenses"
            reason = (
                f"Itemised expenses ({_pence_to_gbp(itemised_pence)}) save more tax than "
                f"trading allowance (£1,000). "
                f"Tax under itemised: {_pence_to_gbp(tax_itemised)} vs "
                f"allowance: {_pence_to_gbp(tax_allowance)}."
            )
            additional_saving = tax_allowance - tax_itemised

        return {
            "recommendation": recommendation,
            "reason": reason,
            "trading_allowance_pence": TRADING_ALLOWANCE_PENCE,
            "itemised_expenses_pence": itemised_pence,
            "tax_saving_trading_allowance_pence": max(0, int(BASIC_RATE * max(0, TRADING_ALLOWANCE_PENCE - itemised_pence))),
            "tax_saving_itemised_pence": int(BASIC_RATE * itemised_pence),
            "additional_saving_pence": additional_saving,
            "additional_saving_gbp": _pence_to_gbp(additional_saving),
        }

    def self_assessment_forecast(self) -> dict[str, Any]:
        """Predict Self Assessment filing requirement, deadlines, and estimated tax/NI due."""
        gross = self._gross_revenue_pence()
        expenses_pence = self._total_approved_expenses_pence()
        ty_start = _tax_year_start()
        ty_end = _tax_year_end(ty_start)
        reg_deadline = _self_assessment_registration_deadline(ty_start)
        pay_deadline = _self_assessment_payment_deadline(ty_start)

        filing_required = gross > TRADING_ALLOWANCE_PENCE

        # Determine best deduction
        if expenses_pence > TRADING_ALLOWANCE_PENCE:
            deduction = expenses_pence
            deduction_type = "itemised_expenses"
        else:
            deduction = TRADING_ALLOWANCE_PENCE
            deduction_type = "trading_allowance"

        taxable_profit = max(0, gross - deduction)
        taxable_income = max(0, taxable_profit - PERSONAL_ALLOWANCE_PENCE)

        # Income tax
        income_tax = int(taxable_income * BASIC_RATE)

        # National Insurance (only if profit > £12,570)
        class_2_ni = CLASS_2_NI_ANNUAL_PENCE if taxable_profit > PERSONAL_ALLOWANCE_PENCE else 0
        class_4_ni_base = max(0, min(taxable_profit, BASIC_RATE_UPPER_PENCE) - PERSONAL_ALLOWANCE_PENCE)
        class_4_ni = int(class_4_ni_base * CLASS_4_NI_RATE)
        total_ni = class_2_ni + class_4_ni

        total_due = income_tax + total_ni

        return {
            "tax_year": f"{ty_start.isoformat()} to {ty_end.isoformat()}",
            "filing_required": filing_required,
            "registration_deadline": reg_deadline.isoformat() if filing_required else None,
            "payment_deadline": pay_deadline.isoformat() if filing_required else None,
            "gross_revenue_pence": gross,
            "gross_revenue_gbp": _pence_to_gbp(gross),
            "deduction_type": deduction_type,
            "deduction_pence": deduction,
            "deduction_gbp": _pence_to_gbp(deduction),
            "taxable_profit_pence": taxable_profit,
            "taxable_profit_gbp": _pence_to_gbp(taxable_profit),
            "personal_allowance_pence": PERSONAL_ALLOWANCE_PENCE,
            "taxable_income_after_personal_allowance_pence": taxable_income,
            "income_tax_pence": income_tax,
            "income_tax_gbp": _pence_to_gbp(income_tax),
            "class_2_ni_pence": class_2_ni,
            "class_4_ni_pence": class_4_ni,
            "total_ni_pence": total_ni,
            "total_tax_and_ni_pence": total_due,
            "total_tax_and_ni_gbp": _pence_to_gbp(total_due),
            "effective_tax_rate_pct": round(total_due / gross * 100, 2) if gross > 0 else 0.0,
        }

    def vat_threshold_forecast(self) -> dict[str, Any]:
        """Track progress to £90,000 VAT threshold and Flat Rate Scheme eligibility."""
        gross = self._gross_revenue_pence()
        remaining = max(0, VAT_THRESHOLD_PENCE - gross)
        pct = round(gross / VAT_THRESHOLD_PENCE * 100, 2)
        mandatory = gross >= VAT_THRESHOLD_PENCE
        flat_rate_eligible = gross < 15_000_000  # £150,000 limit for FRS

        recommendation = []
        if mandatory:
            recommendation.append("VAT registration is mandatory immediately.")
            if flat_rate_eligible:
                recommendation.append(
                    "You are eligible for the VAT Flat Rate Scheme (16.5% of turnover). "
                    "This simplifies accounting and can reduce VAT liability."
                )
        elif gross > VAT_THRESHOLD_PENCE * 0.75:
            recommendation.append(
                f"You are {pct:.1f}% of the way to the £90,000 VAT threshold. "
                "Consider voluntary registration and FRS preparation."
            )
        else:
            recommendation.append(
                f"You are {pct:.1f}% of the way to the £90,000 VAT threshold. "
                "No action required yet."
            )

        return {
            "gross_revenue_pence": gross,
            "gross_revenue_gbp": _pence_to_gbp(gross),
            "vat_threshold_pence": VAT_THRESHOLD_PENCE,
            "vat_threshold_gbp": _pence_to_gbp(VAT_THRESHOLD_PENCE),
            "remaining_to_threshold_pence": remaining,
            "remaining_to_threshold_gbp": _pence_to_gbp(remaining),
            "threshold_pct_used": pct,
            "vat_registration_mandatory": mandatory,
            "flat_rate_scheme_eligible": flat_rate_eligible,
            "flat_rate_pct": VAT_FLAT_RATE * 100,
            "recommendation": " ".join(recommendation),
        }

    def pension_contribution_opportunity(self, amount_pence: int) -> dict[str, Any]:
        """Calculate the tax relief value of a pension contribution."""
        if amount_pence < 0:
            raise ValueError("Pension contribution amount cannot be negative")
        gross = self._gross_revenue_pence()
        expenses_pence = self._total_approved_expenses_pence()
        deduction = max(TRADING_ALLOWANCE_PENCE, expenses_pence)
        taxable_profit = max(0, gross - deduction)

        # Determine applicable marginal rate
        if taxable_profit <= PERSONAL_ALLOWANCE_PENCE:
            marginal_rate = 0.0
        elif taxable_profit <= BASIC_RATE_UPPER_PENCE:
            marginal_rate = BASIC_RATE
        else:
            marginal_rate = 0.40  # higher rate

        tax_relief = int(amount_pence * marginal_rate)
        ni_relief = int(amount_pence * CLASS_4_NI_RATE) if taxable_profit > PERSONAL_ALLOWANCE_PENCE else 0
        total_relief = tax_relief + ni_relief

        return {
            "contribution_pence": amount_pence,
            "contribution_gbp": _pence_to_gbp(amount_pence),
            "marginal_income_tax_rate_pct": marginal_rate * 100,
            "income_tax_relief_pence": tax_relief,
            "income_tax_relief_gbp": _pence_to_gbp(tax_relief),
            "ni_relief_pence": ni_relief,
            "ni_relief_gbp": _pence_to_gbp(ni_relief),
            "total_relief_pence": total_relief,
            "total_relief_gbp": _pence_to_gbp(total_relief),
            "net_cost_pence": max(0, amount_pence - total_relief),
            "net_cost_gbp": _pence_to_gbp(max(0, amount_pence - total_relief)),
        }

    def incorporation_analysis(self) -> dict[str, Any]:
        """Compare sole trader vs. limited company at current profit level."""
        gross = self._gross_revenue_pence()
        expenses_pence = self._total_approved_expenses_pence()
        deduction = max(TRADING_ALLOWANCE_PENCE, expenses_pence)
        taxable_profit = max(0, gross - deduction)

        # Sole trader total tax + NI
        taxable_income = max(0, taxable_profit - PERSONAL_ALLOWANCE_PENCE)
        st_income_tax = int(taxable_income * BASIC_RATE)
        class_4_ni_base = max(0, min(taxable_profit, BASIC_RATE_UPPER_PENCE) - PERSONAL_ALLOWANCE_PENCE)
        st_ni = CLASS_2_NI_ANNUAL_PENCE + int(class_4_ni_base * CLASS_4_NI_RATE) if taxable_profit > PERSONAL_ALLOWANCE_PENCE else 0
        st_total = st_income_tax + st_ni

        # Limited company: 19% Corp Tax on profit, then extract as salary £12,570 (tax-free) + dividends
        lt_corp_tax = int(taxable_profit * CORP_TAX_RATE)
        post_corp_profit = taxable_profit - lt_corp_tax
        # Director salary up to personal allowance (no income tax, small NI)
        director_salary = min(taxable_profit, PERSONAL_ALLOWANCE_PENCE)
        dividends = max(0, post_corp_profit - director_salary)
        taxable_dividends = max(0, dividends - DIVIDEND_ALLOWANCE_PENCE)
        lt_dividend_tax = int(taxable_dividends * 0.0875)  # 8.75% basic rate dividend tax
        lt_total = lt_corp_tax + lt_dividend_tax

        recommend_incorporate = taxable_profit > BASIC_RATE_UPPER_PENCE and lt_total < st_total
        saving = max(0, st_total - lt_total) if recommend_incorporate else 0

        return {
            "taxable_profit_pence": taxable_profit,
            "taxable_profit_gbp": _pence_to_gbp(taxable_profit),
            "sole_trader_total_tax_ni_pence": st_total,
            "sole_trader_total_tax_ni_gbp": _pence_to_gbp(st_total),
            "limited_company_total_tax_pence": lt_total,
            "limited_company_total_tax_gbp": _pence_to_gbp(lt_total),
            "recommend_incorporation": recommend_incorporate,
            "estimated_annual_saving_pence": saving,
            "estimated_annual_saving_gbp": _pence_to_gbp(saving),
            "note": (
                "Incorporation is worth considering when annual profit exceeds £50,270. "
                "Seek professional advice before incorporating."
                if taxable_profit > BASIC_RATE_UPPER_PENCE
                else "Sole trader structure is more efficient at current profit level."
            ),
        }

    def expenses_tracker(self) -> dict[str, Any]:
        """Return all approved expenses grouped by category."""
        rows = self.store.list_expense_logs(approved_only=True)
        by_category: dict[str, int] = {}
        for row in rows:
            cat = row["category"]
            by_category[cat] = by_category.get(cat, 0) + row["amount_pence"]

        total = sum(by_category.values())
        comparison = self.allowable_expenses_vs_allowance()

        return {
            "total_approved_expenses_pence": total,
            "total_approved_expenses_gbp": _pence_to_gbp(total),
            "by_category": {k: {"pence": v, "gbp": _pence_to_gbp(v)} for k, v in by_category.items()},
            "expense_count": len(rows),
            "vs_trading_allowance": comparison,
        }

    def log_expense(self, *, date_str: str, category: str, amount_pence: int,
                    description: str, receipt_ref: str, justification: str) -> dict[str, Any]:
        """K-2SO-authorised logging of a business expense.

        K-2SO verifies the expense is a legitimate HMRC-allowable business cost.
        Returns approval decision with audit trail entry.
        """
        if category not in ALLOWABLE_CATEGORIES:
            return {
                "approved": False,
                "reason": (
                    f"Category '{category}' is not an HMRC-allowable expense category. "
                    f"Valid categories: {sorted(ALLOWABLE_CATEGORIES)}"
                ),
                "expense_id": None,
            }

        if amount_pence <= 0:
            return {
                "approved": False,
                "reason": "Expense amount must be positive.",
                "expense_id": None,
            }

        if not receipt_ref.strip():
            return {
                "approved": False,
                "reason": "K-2SO requires a receipt reference or justification document.",
                "expense_id": None,
            }

        if not justification.strip():
            return {
                "approved": False,
                "reason": "K-2SO requires a business justification for this expense.",
                "expense_id": None,
            }

        expense_id = str(uuid.uuid4())
        self.store.add_expense_log(
            expense_id=expense_id,
            date=date_str,
            category=category,
            amount_pence=amount_pence,
            description=description,
            receipt_ref=receipt_ref,
            justification=justification,
            approved_by="K-2SO",
            approved=True,
        )
        self.store.log(
            "K-2SO",
            "expense_approved",
            {
                "expense_id": expense_id,
                "category": category,
                "amount_gbp": _pence_to_gbp(amount_pence),
                "justification": justification,
            },
        )

        return {
            "approved": True,
            "expense_id": expense_id,
            "category": category,
            "amount_pence": amount_pence,
            "amount_gbp": _pence_to_gbp(amount_pence),
            "approved_by": "K-2SO",
            "reason": "Expense approved: legitimate HMRC-allowable business cost with receipt reference.",
        }

    def tax_year_summary(self) -> dict[str, Any]:
        """Year-end tax position summary."""
        sa = self.self_assessment_forecast()
        comparison = self.allowable_expenses_vs_allowance()
        gross = self._gross_revenue_pence()
        total_expenses = self._total_approved_expenses_pence()

        return {
            "tax_year": sa["tax_year"],
            "gross_revenue_pence": sa["gross_revenue_pence"],
            "gross_revenue_gbp": sa["gross_revenue_gbp"],
            "itemised_expenses_pence": total_expenses,
            "itemised_expenses_gbp": _pence_to_gbp(total_expenses),
            "deduction_recommended": comparison["recommendation"],
            "deduction_applied_pence": sa["deduction_pence"],
            "deduction_applied_gbp": sa["deduction_gbp"],
            "taxable_profit_pence": sa["taxable_profit_pence"],
            "taxable_profit_gbp": sa["taxable_profit_gbp"],
            "personal_allowance_pence": PERSONAL_ALLOWANCE_PENCE,
            "personal_allowance_gbp": _pence_to_gbp(PERSONAL_ALLOWANCE_PENCE),
            "taxable_income_after_personal_allowance_pence": sa["taxable_income_after_personal_allowance_pence"],
            "income_tax_due_pence": sa["income_tax_pence"],
            "income_tax_due_gbp": sa["income_tax_gbp"],
            "class_2_ni_pence": sa["class_2_ni_pence"],
            "class_4_ni_pence": sa["class_4_ni_pence"],
            "total_ni_pence": sa["total_ni_pence"],
            "total_tax_and_ni_pence": sa["total_tax_and_ni_pence"],
            "total_tax_and_ni_gbp": sa["total_tax_and_ni_gbp"],
            "effective_tax_rate_pct": sa["effective_tax_rate_pct"],
            "filing_required": sa["filing_required"],
            "registration_deadline": sa["registration_deadline"],
            "payment_deadline": sa["payment_deadline"],
        }
