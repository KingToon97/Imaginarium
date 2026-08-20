from __future__ import annotations

import os
from typing import Any
from urllib.parse import urljoin

import requests


DEFAULT_API_URL = os.getenv("IMAGINARIUM_API_URL", "http://localhost:8000/")


def format_currency(amount_pence: int | float | None) -> str:
    amount = 0 if amount_pence is None else float(amount_pence)
    return f"£{amount / 100:.2f}"


def _base_url(base_url: str | None = None) -> str:
    chosen = (base_url or DEFAULT_API_URL).strip()
    return chosen if chosen.endswith("/") else f"{chosen}/"


def fetch_json(path: str, *, base_url: str | None = None, params: dict[str, Any] | None = None, timeout: int = 10) -> dict[str, Any]:
    response = requests.get(urljoin(_base_url(base_url), path.lstrip("/")), params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def fetch_revenue_summary(base_url: str | None = None) -> dict[str, Any]:
    return fetch_json("/api/v1/revenue/summary", base_url=base_url)


def fetch_products(base_url: str | None = None) -> dict[str, Any]:
    return fetch_json("/api/v1/revenue/products", base_url=base_url)


def fetch_forecast(base_url: str | None = None) -> dict[str, Any]:
    return fetch_json("/api/v1/revenue/forecast", base_url=base_url)


def fetch_agents(base_url: str | None = None) -> dict[str, Any]:
    return fetch_json("/api/v1/agents/roster", base_url=base_url)


def fetch_activity(
    base_url: str | None = None,
    *,
    event_type: str | None = None,
    days: int = 30,
    limit: int = 50,
) -> dict[str, Any]:
    params: dict[str, Any] = {"days": days, "limit": limit}
    if event_type and event_type != "all":
        params["event_type"] = event_type
    return fetch_json("/api/v1/activity/feed", base_url=base_url, params=params)


def load_dashboard_bundle(base_url: str | None = None, *, activity_type: str | None = None, activity_days: int = 30) -> dict[str, Any]:
    return {
        "summary": fetch_revenue_summary(base_url),
        "products": fetch_products(base_url),
        "forecast": fetch_forecast(base_url),
        "agents": fetch_agents(base_url),
        "activity": fetch_activity(base_url, event_type=activity_type, days=activity_days),
    }
