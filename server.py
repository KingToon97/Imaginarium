"""HTTP server for Imaginarium.

Exposes the pipeline as a REST API so the app can be deployed behind any
WSGI/ASGI-compatible host (Uvicorn, Gunicorn+Uvicorn, etc.).

Endpoints
---------
GET  /healthz                         — liveness probe
GET  /status                          — treasury balance + agent roster
POST /execute                         — run a business idea through the pipeline
GET  /tax-status                      — current tax position and alerts
GET  /tax-compliance/forecast         — Self Assessment forecast and filing requirements
GET  /tax-compliance/expenses         — all approved expense logs and totals
POST /tax-compliance/log-expense      — K-2SO authorised expense logging
GET  /tax-compliance/efficiency       — tax efficiency recommendations
GET  /tax-compliance/vat-forecast     — progress to £90k VAT threshold
GET  /tax-compliance/audit-trail      — complete tax decision audit trail
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .app import Imaginarium

# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------

_app: Imaginarium | None = None


@asynccontextmanager
async def lifespan(server: FastAPI):
    global _app
    _app = Imaginarium(home=os.getenv("IMAGINARIUM_HOME", "./runtime"))
    yield
    # cleanup (sqlite closes on GC, nothing else to tear down)
    _app = None


server = FastAPI(
    title="Imaginarium",
    description="Bounded autonomous multi-agent business engine",
    version="3.2.0",
    lifespan=lifespan,
)


def _get_app() -> Imaginarium:
    if _app is None:  # pragma: no cover
        raise HTTPException(status_code=503, detail="App not initialised")
    return _app


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class IdeaRequest(BaseModel):
    title: str = Field(..., description="Short product/service title")
    description: str = Field(..., description="Full product description")
    channel: str = Field("local storefront", description="Distribution channel")
    expected_revenue_pence: int = Field(..., ge=0)
    expected_cost_pence: int = Field(0, ge=0)
    vulnerability_risk: str = Field("low", pattern="^(none|low|medium|high)$")
    legal_confidence: float = Field(1.0, ge=0.0, le=1.0)
    customer_value: float = Field(0.5, ge=0.0, le=1.0)
    probability_of_sale: float = Field(0.1, ge=0.0, le=1.0)
    hours_to_launch: float = Field(1.0, gt=0)


class StatusResponse(BaseModel):
    balance_pence: int
    balance_gbp: str
    agents: list[dict[str, Any]]


class LogExpenseRequest(BaseModel):
    date: str = Field(..., description="Expense date (YYYY-MM-DD)")
    category: str = Field(
        ...,
        description=(
            "HMRC-allowable category: home_office | software | hosting | domain | "
            "marketing | professional_dev | equipment"
        ),
    )
    amount_pence: int = Field(..., gt=0, description="Expense amount in pence")
    description: str = Field(..., description="Brief description of the expense")
    receipt_ref: str = Field(..., description="Receipt identifier, URL, or reference number")
    justification: str = Field(..., description="Business justification for the expense")


# ---------------------------------------------------------------------------
# Routes — core
# ---------------------------------------------------------------------------


@server.get("/healthz", tags=["ops"])
def healthz() -> JSONResponse:
    """Liveness probe — always returns 200 if the process is up."""
    return JSONResponse({"status": "ok"})


@server.get("/status", response_model=StatusResponse, tags=["ops"])
def status() -> StatusResponse:
    """Treasury balance and agent morale roster."""
    app = _get_app()
    balance = app.store.balance()
    agents = app.store.agents()
    return StatusResponse(
        balance_pence=balance,
        balance_gbp=f"£{balance / 100:.2f}",
        agents=agents,
    )


@server.post("/execute", tags=["pipeline"])
def execute(idea: IdeaRequest) -> JSONResponse:
    """Run a business idea through the full agent pipeline."""
    app = _get_app()
    result = app.execute(idea.model_dump())
    return JSONResponse(result)


# ---------------------------------------------------------------------------
# Routes — tax compliance
# ---------------------------------------------------------------------------


@server.get("/tax-status", tags=["tax"])
def tax_status() -> JSONResponse:
    """Current HMRC tax position: trading allowance used, phase, filing deadlines, alerts."""
    app = _get_app()
    return JSONResponse(app.tax.trading_allowance_status())


@server.get("/tax-compliance/forecast", tags=["tax"])
def tax_forecast() -> JSONResponse:
    """12-month Self Assessment forecast: filing requirements, deadlines, estimated tax/NI due."""
    app = _get_app()
    return JSONResponse(app.tax.self_assessment_forecast())


@server.get("/tax-compliance/expenses", tags=["tax"])
def tax_expenses() -> JSONResponse:
    """All K-2SO approved allowable expenses, totals, and comparison vs. trading allowance."""
    app = _get_app()
    return JSONResponse(app.tax.expenses_tracker())


@server.post("/tax-compliance/log-expense", tags=["tax"])
def tax_log_expense(req: LogExpenseRequest) -> JSONResponse:
    """K-2SO authorised logging of a business expense.

    K-2SO verifies the expense is a legitimate HMRC-allowable business cost
    with a receipt reference and business justification before approving.
    """
    app = _get_app()
    result = app.tax.log_expense(
        date_str=req.date,
        category=req.category,
        amount_pence=req.amount_pence,
        description=req.description,
        receipt_ref=req.receipt_ref,
        justification=req.justification,
    )
    status_code = 200 if result["approved"] else 400
    return JSONResponse(result, status_code=status_code)


@server.get("/tax-compliance/efficiency", tags=["tax"])
def tax_efficiency() -> JSONResponse:
    """Tax efficiency recommendations: trading allowance vs. itemised, pension, equipment allowance."""
    app = _get_app()
    expenses_comparison = app.tax.allowable_expenses_vs_allowance()
    vat = app.tax.vat_threshold_forecast()
    incorporation = app.tax.incorporation_analysis()
    gross = app.store.gross_revenue()

    recommendations = []

    # Trading allowance vs. itemised
    rec = expenses_comparison["recommendation"]
    if rec == "itemised_expenses":
        saving = expenses_comparison["additional_saving_gbp"]
        recommendations.append(
            f"Claim itemised expenses instead of trading allowance to save an additional {saving} in tax."
        )
    else:
        recommendations.append(
            "Use the £1,000 trading allowance — it saves more tax than your current itemised expenses."
        )

    # Pension
    if gross > 1_257_000:  # above personal allowance
        recommendations.append(
            "Consider personal pension contributions — 100% tax-deductible, "
            "reduces taxable profit pound-for-pound at your marginal rate."
        )

    # Equipment allowance
    recommendations.append(
        "Any equipment or software purchases qualify for 100% Annual Investment Allowance "
        "(AIA limit £1,000,000) — fully deductible in year of purchase."
    )

    # Home office
    recommendations.append(
        "If working from home, claim 10% of rent/mortgage interest as home office expense."
    )

    # Incorporation
    if incorporation["recommend_incorporation"]:
        saving = incorporation["estimated_annual_saving_gbp"]
        recommendations.append(
            f"Consider limited company incorporation: estimated annual tax saving of {saving}. "
            "Seek professional advice before proceeding."
        )

    # VAT FRS
    if vat["vat_registration_mandatory"] and vat["flat_rate_scheme_eligible"]:
        recommendations.append(
            "VAT registration mandatory. Register for VAT Flat Rate Scheme (16.5%) to simplify "
            "accounting and potentially reduce VAT liability."
        )

    return JSONResponse(
        {
            "recommendations": recommendations,
            "expenses_comparison": expenses_comparison,
            "vat_summary": {
                "mandatory": vat["vat_registration_mandatory"],
                "flat_rate_eligible": vat["flat_rate_scheme_eligible"],
                "threshold_pct_used": vat["threshold_pct_used"],
            },
            "incorporation_summary": {
                "recommend": incorporation["recommend_incorporation"],
                "note": incorporation["note"],
            },
        }
    )


@server.get("/tax-compliance/vat-forecast", tags=["tax"])
def tax_vat_forecast() -> JSONResponse:
    """Progress to £90,000 VAT registration threshold and Flat Rate Scheme eligibility."""
    app = _get_app()
    return JSONResponse(app.tax.vat_threshold_forecast())


@server.get("/tax-compliance/audit-trail", tags=["tax"])
def tax_audit_trail() -> JSONResponse:
    """Complete audit trail of all tax-related decisions, expense approvals, and calculations."""
    app = _get_app()
    rows = app.store.db.execute(
        "SELECT ts, agent, action, payload FROM audit ORDER BY ts DESC LIMIT 500"
    ).fetchall()
    entries = [
        {
            "timestamp": row["ts"],
            "agent": row["agent"],
            "action": row["action"],
            "payload": row["payload"],
        }
        for row in rows
    ]
    return JSONResponse({"audit_trail": entries, "count": len(entries)})

