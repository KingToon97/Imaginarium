"""HTTP server for Imaginarium.

Exposes the pipeline as a REST API so the app can be deployed behind any
WSGI/ASGI-compatible host (Uvicorn, Gunicorn+Uvicorn, etc.).

Endpoints
---------
GET  /healthz                         — liveness probe
GET  /status                          — treasury balance + agent roster
POST /execute                         — run a business idea through the pipeline
GET  /api/v1/revenue/summary         — dashboard revenue summary
GET  /api/v1/revenue/products        — dashboard product performance
GET  /api/v1/revenue/forecast        — dashboard forecast and what-if scenarios
GET  /api/v1/agents/roster           — dashboard agent morale and activity
GET  /api/v1/activity/feed           — dashboard activity feed
GET  /tax-status                      — current tax position and alerts
GET  /tax-compliance/forecast         — Self Assessment forecast and filing requirements
GET  /tax-compliance/expenses         — all approved expense logs and totals
POST /tax-compliance/log-expense      — K-2SO authorised expense logging
GET  /tax-compliance/efficiency       — tax efficiency recommendations
GET  /tax-compliance/vat-forecast     — progress to £90k VAT threshold
GET  /tax-compliance/audit-trail      — complete tax decision audit trail
"""
from __future__ import annotations

import json
import os
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .app import Imaginarium
from .tax_compliance import PERSONAL_ALLOWANCE_PENCE

TRADING_ALLOWANCE_PENCE = 100_000
VAT_REGISTRATION_THRESHOLD_PENCE = 9_000_000

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


def _parse_ts(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _currency(amount_pence: int | float) -> str:
    return f"£{float(amount_pence) / 100:.2f}"


def _pct(part: int | float, total: int | float) -> float:
    return round((float(part) / float(total)) * 100, 2) if total else 0.0


def _pct_change(current: int, previous: int) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 2)


def _tax_year_start(now: datetime) -> datetime:
    year = now.year - 1 if (now.month, now.day) < (4, 6) else now.year
    return datetime(year, 4, 6, tzinfo=timezone.utc)


def _deadline(month: int, day: int, now: datetime) -> datetime:
    candidate = datetime(now.year, month, day, tzinfo=timezone.utc)
    if candidate.date() < now.date():
        candidate = datetime(now.year + 1, month, day, tzinfo=timezone.utc)
    return candidate


def _days_remaining(future: datetime, now: datetime) -> int:
    return max(0, (future.date() - now.date()).days)


def _ledger_windows(app: Imaginarium) -> tuple[datetime, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    now = datetime.now(timezone.utc)
    ledger = [{**entry, "dt": _parse_ts(entry["ts"])} for entry in app.store.ledger_entries()]
    sales = [{**sale, "dt": _parse_ts(sale["ts"])} for sale in app.store.sales()]
    proposals = app.store.proposals()
    return now, ledger, sales, proposals


def _tax_window_totals(
    app: Imaginarium,
    *,
    now: datetime | None = None,
    ledger: list[dict[str, Any]] | None = None,
    sales: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    if now is None or ledger is None or sales is None:
        now, ledger, sales, _ = _ledger_windows(app)
    tax_year_start = _tax_year_start(now)
    revenue_entries = [entry for entry in ledger if int(entry["amount_pence"]) > 0]
    expense_entries = [entry for entry in ledger if int(entry["amount_pence"]) < 0]
    gross_tax_year = (
        int(sum(int(row["gross_pence"]) for row in sales if row["dt"] >= tax_year_start))
        if sales
        else int(sum(int(row["amount_pence"]) for row in revenue_entries if row["dt"] >= tax_year_start))
    )
    expenses_tax_year = abs(int(sum(int(row["amount_pence"]) for row in expense_entries if row["dt"] >= tax_year_start)))
    return {"gross_tax_year": gross_tax_year, "expenses_tax_year": expenses_tax_year}


def _product_metrics(app: Imaginarium) -> dict[str, Any]:
    now, _ledger, sales, proposals = _ledger_windows(app)
    current_month = (now.year, now.month)
    sales_by_product: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "sales_all_time": 0,
        "sales_this_month": 0,
        "revenue_all_time_pence": 0,
        "revenue_this_month_pence": 0,
        "gross_all_time_pence": 0,
    })
    for sale in sales:
        bucket = sales_by_product[sale["proposal_id"]]
        bucket["sales_all_time"] += 1
        bucket["revenue_all_time_pence"] += int(sale["net_pence"])
        bucket["gross_all_time_pence"] += int(sale["gross_pence"])
        if (sale["dt"].year, sale["dt"].month) == current_month:
            bucket["sales_this_month"] += 1
            bucket["revenue_this_month_pence"] += int(sale["net_pence"])

    products: list[dict[str, Any]] = []
    for proposal in proposals:
        metrics = sales_by_product[proposal["id"]]
        created_at = _parse_ts(proposal["created_at"])
        average_price = 0
        if metrics["sales_all_time"]:
            average_price = round(metrics["gross_all_time_pence"] / metrics["sales_all_time"])
        elif proposal.get("expected_revenue_pence"):
            average_price = int(proposal["expected_revenue_pence"])
        product = {
            "proposal_id": proposal["id"],
            "product_name": proposal.get("title", proposal["id"]),
            "status": proposal.get("status", "unknown"),
            "created_at": proposal["created_at"],
            "sales_count_this_month": metrics["sales_this_month"],
            "sales_count_all_time": metrics["sales_all_time"],
            "revenue_this_month_pence": metrics["revenue_this_month_pence"],
            "revenue_all_time_pence": metrics["revenue_all_time_pence"],
            "average_price_pence": average_price,
            "conversion_rate": None,
            "customer_feedback_rating": None,
            "is_new": (now - created_at).days <= 14,
            "is_underperformer": proposal.get("status") == "live" and metrics["sales_all_time"] == 0 and (now - created_at).days > 14,
        }
        products.append(product)

    products.sort(key=lambda item: (-item["revenue_all_time_pence"], item["product_name"]))
    return {
        "products": products,
        "top_performers": products[:5],
        "new_products": [product for product in products if product["is_new"]][:5],
        "underperformers": [product for product in products if product["is_underperformer"]][:5],
    }


def _agent_metrics(app: Imaginarium) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    agents = app.store.agents()
    audits = app.store.audit_events(limit=1000)
    rewards = [{**reward, "dt": _parse_ts(reward["ts"])} for reward in app.store.reward_events()]
    current_month = (now.year, now.month)

    latest_activity: dict[str, datetime] = {}
    tasks_completed: dict[str, int] = defaultdict(int)
    for event in audits:
        agent_name = event["agent"]
        dt = _parse_ts(event["ts"])
        if agent_name not in latest_activity or dt > latest_activity[agent_name]:
            latest_activity[agent_name] = dt
        if (dt.year, dt.month) == current_month:
            tasks_completed[agent_name] += 1

    reward_totals: dict[str, int] = defaultdict(int)
    reward_by_day: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for reward in rewards:
        reward_totals[reward["agent_id"]] += int(reward["points"])
        reward_by_day[reward["dt"].date().isoformat()][reward["agent_id"]] += int(reward["points"])

    roster: list[dict[str, Any]] = []
    total_net_revenue = sum(int(sale["net_pence"]) for sale in app.store.sales())
    for agent in agents:
        display_name = agent["display_name"]
        roster.append({
            "agent_id": agent["agent_id"],
            "agent_name": display_name,
            "role": agent["role"],
            "morale_score": agent["morale"],
            "tasks_completed_this_month": tasks_completed.get(display_name, 0),
            "last_active": latest_activity.get(display_name).isoformat() if latest_activity.get(display_name) else None,
            "contribution_to_revenue_pence": total_net_revenue if agent["agent_id"] == "tars" and total_net_revenue else None,
            "alert": "Hydra watch" if agent["morale"] < 40 else None,
        })

    dates = [(now.date() - timedelta(days=offset)).isoformat() for offset in range(29, -1, -1)]
    morale_baseline = {
        agent["agent_id"]: agent["morale"] - reward_totals.get(agent["agent_id"], 0)
        for agent in agents
    }
    cumulative = morale_baseline.copy()
    morale_trend: list[dict[str, Any]] = []
    for day in dates:
        for agent_id, points in reward_by_day.get(day, {}).items():
            cumulative[agent_id] = cumulative.get(agent_id, 100) + points
        average_morale = round(
            sum(cumulative.get(agent["agent_id"], agent["morale"]) for agent in agents) / max(len(agents), 1),
            2,
        )
        morale_trend.append({"date": day, "average_morale": average_morale})

    return {"agents": roster, "morale_trend": morale_trend}


def _low_morale_agents(app: Imaginarium) -> list[dict[str, Any]]:
    return [agent for agent in app.store.agents() if agent["morale"] < 40]


def _activity_feed(app: Imaginarium, event_type: str | None = None, days: int = 30, limit: int = 50) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max(days, 1))
    items: list[dict[str, Any]] = []

    for entry in app.store.ledger_entries():
        dt = _parse_ts(entry["ts"])
        if dt < cutoff:
            continue
        category = "sales" if entry["amount_pence"] > 0 else "expenses"
        if event_type and category != event_type:
            continue
        amount = abs(int(entry["amount_pence"]))
        items.append({
            "timestamp": entry["ts"],
            "type": category,
            "actor": "Treasury" if category == "expenses" else "Sales",
            "headline": ("Revenue received" if category == "sales" else "Expense authorised"),
            "details": entry["memo"],
            "amount_pence": amount,
            "amount_gbp": _currency(amount),
        })

    for event in app.store.audit_events(limit=500):
        dt = _parse_ts(event["ts"])
        if dt < cutoff:
            continue
        action = event["action"]
        category = "agent"
        if action == "publish":
            category = "product"
        elif action in {"sale_recorded"}:
            category = "sales"
        elif action in {"marketing_asset"}:
            category = "marketing"
        if event_type and category != event_type:
            continue
        try:
            payload = json.loads(event["payload"])
        except json.JSONDecodeError:
            payload = {"raw": event["payload"]}
        items.append({
            "timestamp": event["ts"],
            "type": category,
            "actor": event["agent"],
            "headline": action.replace("_", " ").title(),
            "details": payload,
        })

    gross_tax_year = _tax_window_totals(app)["gross_tax_year"]
    if gross_tax_year >= TRADING_ALLOWANCE_PENCE and (not event_type or event_type == "tax"):
        items.append({
            "timestamp": now.isoformat(),
            "type": "tax",
            "actor": "HMRC monitor",
            "headline": "Trading allowance exceeded",
            "details": "Self Assessment registration should be tracked and trading allowance is no longer sufficient.",
        })

    items.sort(key=lambda item: item["timestamp"], reverse=True)
    return {"items": items[:limit]}


def _revenue_summary(app: Imaginarium) -> dict[str, Any]:
    now, ledger, sales, _proposals = _ledger_windows(app)
    revenue_entries = [entry for entry in ledger if int(entry["amount_pence"]) > 0]
    expense_entries = [entry for entry in ledger if int(entry["amount_pence"]) < 0]
    current_balance = app.store.balance()

    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    week_start = now - timedelta(days=7)
    previous_week_start = week_start - timedelta(days=7)
    month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    last_month_end = month_start
    last_month_start = datetime(last_month_end.year - (1 if last_month_end.month == 1 else 0), 12 if last_month_end.month == 1 else last_month_end.month - 1, 1, tzinfo=timezone.utc)
    year_start = datetime(now.year, 1, 1, tzinfo=timezone.utc)
    tax_year_start = _tax_year_start(now)

    def _sum_amount(rows: list[dict[str, Any]], start: datetime, end: datetime | None = None) -> int:
        return int(sum(
            int(row["amount_pence"])
            for row in rows
            if row["dt"] >= start and (end is None or row["dt"] < end)
        ))

    def _sum_sales(key: str, start: datetime, end: datetime | None = None) -> int:
        return int(sum(
            int(row[key])
            for row in sales
            if row["dt"] >= start and (end is None or row["dt"] < end)
        ))

    today_net = _sum_amount(revenue_entries, today_start)
    week_net = _sum_amount(revenue_entries, week_start)
    previous_week_net = _sum_amount(revenue_entries, previous_week_start, week_start)
    month_net = _sum_amount(revenue_entries, month_start)
    last_month_net = _sum_amount(revenue_entries, last_month_start, last_month_end)
    ytd_net = _sum_amount(revenue_entries, year_start)
    ytd_gross = _sum_sales("gross_pence", year_start) if sales else ytd_net
    tax_totals = _tax_window_totals(app, now=now, ledger=ledger, sales=sales)
    gross_tax_year = tax_totals["gross_tax_year"]
    expenses_tax_year = tax_totals["expenses_tax_year"]
    month_expenses = abs(_sum_amount(expense_entries, month_start))
    daily_velocity = round(month_net / max(now.day, 1))
    weekly_velocity = week_net
    monthly_velocity = daily_velocity * 30
    profit_margin = _pct(ytd_net, ytd_gross)
    burn_rate = round(month_expenses / max(now.day, 1))

    preferred_deduction = "expenses" if expenses_tax_year > TRADING_ALLOWANCE_PENCE else "trading_allowance"
    deductible_amount = expenses_tax_year if preferred_deduction == "expenses" else TRADING_ALLOWANCE_PENCE
    taxable_profit = max(0, gross_tax_year - deductible_amount)
    estimated_income_tax = int(max(0, taxable_profit - PERSONAL_ALLOWANCE_PENCE) * 0.2)
    vat_threshold = VAT_REGISTRATION_THRESHOLD_PENCE

    registration_deadline = _deadline(10, 5, now)
    filing_deadline = _deadline(1, 31, now)
    vat_deadline = now if gross_tax_year >= vat_threshold else None

    lifetime_net = sum(int(entry["amount_pence"]) for entry in revenue_entries)
    milestone_specs = (
        ("First £1", 100, lifetime_net, "lifetime"),
        ("£10/day", 1_000, daily_velocity, "daily"),
        ("£25/day", 2_500, daily_velocity, "daily"),
        ("£100/day", 10_000, daily_velocity, "daily"),
        ("£1,000/month", 100_000, monthly_velocity, "monthly"),
    )
    milestones: list[dict[str, Any]] = []
    for label, target, current, cadence in milestone_specs:
        remaining = max(0, target - current)
        eta_days = None if current <= 0 or remaining == 0 else int((remaining + current - 1) // current)
        milestones.append({
            "label": label,
            "target_pence": target,
            "target_gbp": _currency(target),
            "current_pence": current,
            "current_gbp": _currency(current),
            "progress_pct": round(min(100.0, (current / target) * 100), 2) if target else 100.0,
            "remaining_pence": remaining,
            "remaining_gbp": _currency(remaining),
            "achieved": current >= target,
            "cadence": cadence,
            "eta_days": eta_days,
            "projected_date": (now + timedelta(days=eta_days)).date().isoformat() if eta_days is not None else None,
        })

    tax_position = "Tax-free under trading allowance"
    if gross_tax_year > TRADING_ALLOWANCE_PENCE:
        tax_position = f"Self Assessment likely required by {registration_deadline.date().isoformat()}"
    if estimated_income_tax > 0:
        tax_position = "Estimated income tax likely due (basic-rate assumption)"
    if gross_tax_year >= vat_threshold:
        tax_position = "VAT registration threshold reached — register immediately"

    alerts: list[dict[str, str]] = []
    achieved_milestones = [milestone["label"] for milestone in milestones if milestone["achieved"]]
    if achieved_milestones:
        alerts.append({"type": "revenue", "message": f"Milestones achieved: {', '.join(achieved_milestones)}"})
    if gross_tax_year > TRADING_ALLOWANCE_PENCE:
        alerts.append({
            "type": "tax",
            "message": f"Trading allowance exceeded; track Self Assessment registration by {registration_deadline.date().isoformat()}",
        })
    if gross_tax_year >= vat_threshold:
        alerts.append({"type": "tax", "message": "VAT registration threshold reached — register immediately."})
    for agent in _low_morale_agents(app):
        alerts.append({"type": "agent", "message": f"{agent['display_name']} morale below 40 — consider intervention."})

    return {
        "generated_at": now.isoformat(),
        "current_balance_pence": current_balance,
        "current_balance_gbp": _currency(current_balance),
        "revenue": {
            "today_net_pence": today_net,
            "today_net_gbp": _currency(today_net),
            "week_net_pence": week_net,
            "week_net_gbp": _currency(week_net),
            "week_change_pct": _pct_change(week_net, previous_week_net),
            "month_net_pence": month_net,
            "month_net_gbp": _currency(month_net),
            "month_change_pct": _pct_change(month_net, last_month_net),
            "last_month_net_pence": last_month_net,
            "last_month_net_gbp": _currency(last_month_net),
            "ytd_gross_pence": ytd_gross,
            "ytd_gross_gbp": _currency(ytd_gross),
            "ytd_net_pence": ytd_net,
            "ytd_net_gbp": _currency(ytd_net),
            "velocity": {
                "daily_pence": daily_velocity,
                "weekly_pence": weekly_velocity,
                "monthly_pence": monthly_velocity,
                "daily_gbp": _currency(daily_velocity),
                "weekly_gbp": _currency(weekly_velocity),
                "monthly_gbp": _currency(monthly_velocity),
                "trend": "up" if week_net >= previous_week_net else "down",
            },
        },
        "milestones": milestones,
        "tax": {
            "trading_allowance_used_pence": gross_tax_year,
            "trading_allowance_used_gbp": _currency(gross_tax_year),
            "trading_allowance_limit_pence": TRADING_ALLOWANCE_PENCE,
            "trading_allowance_remaining_pence": max(0, TRADING_ALLOWANCE_PENCE - gross_tax_year),
            "trading_allowance_progress_pct": _pct(min(gross_tax_year, TRADING_ALLOWANCE_PENCE), TRADING_ALLOWANCE_PENCE),
            "position": tax_position,
            "estimated_tax_due_pence": estimated_income_tax,
            "estimated_tax_due_gbp": _currency(estimated_income_tax),
            "deduction_strategy": preferred_deduction,
            "deduction_strategy_note": "Use the larger of the £1,000 trading allowance or allowable business expenses; do not claim both.",
            "expenses_claimed_pence": expenses_tax_year,
            "expenses_claimed_gbp": _currency(expenses_tax_year),
            "deadlines": {
                "self_assessment_registration": {
                    "date": registration_deadline.date().isoformat(),
                    "days_remaining": _days_remaining(registration_deadline, now),
                },
                "self_assessment_filing": {
                    "date": filing_deadline.date().isoformat(),
                    "days_remaining": _days_remaining(filing_deadline, now),
                },
                "vat_registration": {
                    "date": vat_deadline.date().isoformat() if vat_deadline else None,
                    "days_remaining": 0 if vat_deadline else None,
                },
            },
            "vat_turnover_progress_pct": _pct(min(gross_tax_year, vat_threshold), vat_threshold),
            "assumptions": [
                "Income-tax estimate assumes this business is your only income and applies a basic 20% rate above the personal allowance.",
                "HMRC deadlines are informational only; confirm your exact filing obligations before submitting returns.",
            ],
        },
        "financial_health": {
            "profit_margin_pct": profit_margin,
            "burn_rate_pence_per_day": burn_rate,
            "burn_rate_gbp_per_day": _currency(burn_rate),
            "reinvestment_ratio_pct": round(app.treasury.reinvestment_rate * 100, 2),
            "reinvestment_budget_pence": app.treasury.reinvestment_budget(),
            "reinvestment_budget_gbp": _currency(app.treasury.reinvestment_budget()),
            "available_cash_pence": current_balance,
            "available_cash_gbp": _currency(current_balance),
            "runway_days": round(app.treasury.reinvestment_budget() / burn_rate, 1) if burn_rate else None,
        },
        "alerts": alerts,
    }


def _forecast(app: Imaginarium) -> dict[str, Any]:
    summary = _revenue_summary(app)
    now = datetime.now(timezone.utc)
    daily_velocity = summary["revenue"]["velocity"]["daily_pence"]

    def _eta_for_target(target_pence: int, multiplier: float = 1.0) -> dict[str, Any]:
        projected_daily = int(daily_velocity * multiplier)
        meets_target = projected_daily >= target_pence and projected_daily > 0
        return {
            "target_pence": target_pence,
            "target_gbp": _currency(target_pence),
            "projected_daily_velocity_pence": projected_daily,
            "projected_daily_velocity_gbp": _currency(projected_daily),
            "meets_target_immediately": meets_target,
            "eta_days": 0 if meets_target else None,
            "projected_date": now.date().isoformat() if meets_target else None,
        }

    projections = []
    for horizon in (7, 30, 90):
        projected = daily_velocity * horizon
        projections.append({
            "days": horizon,
            "projected_revenue_pence": projected,
            "projected_revenue_gbp": _currency(projected),
        })

    return {
        "daily_velocity_pence": daily_velocity,
        "daily_velocity_gbp": _currency(daily_velocity),
        "projections": projections,
        "milestone_etas": summary["milestones"],
        "what_if_scenarios": [
            {
                "name": "Increase marketing spend by 20%",
                "assumption": "Assumes a 20% lift in revenue velocity from better reach.",
                **_eta_for_target(2_500, multiplier=1.2),
            },
            {
                "name": "Improve conversion by 10%",
                "assumption": "Assumes a 10% lift in revenue velocity from better conversion.",
                **_eta_for_target(10_000, multiplier=1.1),
            },
        ],
    }


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


@server.get("/api/v1/revenue/summary", tags=["dashboard"])
def revenue_summary() -> JSONResponse:
    app = _get_app()
    return JSONResponse(_revenue_summary(app))


@server.get("/api/v1/revenue/products", tags=["dashboard"])
def revenue_products() -> JSONResponse:
    app = _get_app()
    return JSONResponse(_product_metrics(app))


@server.get("/api/v1/revenue/forecast", tags=["dashboard"])
def revenue_forecast() -> JSONResponse:
    app = _get_app()
    return JSONResponse(_forecast(app))


@server.get("/api/v1/agents/roster", tags=["dashboard"])
def agents_roster() -> JSONResponse:
    app = _get_app()
    return JSONResponse(_agent_metrics(app))


@server.get("/api/v1/activity/feed", tags=["dashboard"])
def activity_feed(
    event_type: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    limit: int = Query(default=50, ge=1, le=200),
) -> JSONResponse:
    app = _get_app()
    return JSONResponse(_activity_feed(app, event_type=event_type, days=days, limit=limit))


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
    if gross > PERSONAL_ALLOWANCE_PENCE:
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
    rows = app.store.list_audit_trail(limit=500)
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
