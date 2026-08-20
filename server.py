"""HTTP server for Imaginarium.

Exposes the pipeline as a REST API so the app can be deployed behind any
WSGI/ASGI-compatible host (Uvicorn, Gunicorn+Uvicorn, etc.).

Endpoints
---------
GET  /healthz          — liveness probe
GET  /status           — treasury balance + agent roster
POST /execute          — run a business idea through the pipeline
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


# ---------------------------------------------------------------------------
# Routes
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
