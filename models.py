from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass
class Proposal:
    id: str
    title: str
    description: str
    channel: str
    expected_revenue_pence: int
    expected_cost_pence: int
    vulnerability_risk: str = "low"
    legal_confidence: float = 1.0
    customer_value: float = 0.5
    probability_of_sale: float = 0.1
    hours_to_launch: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class Verdict:
    approved: bool
    reasons: list[str] = field(default_factory=list)

@dataclass
class AgentRecord:
    agent_id: str
    lineage: str
    display_name: str
    role: str
    generation: int
    status: str
    morale: int
    parent_id: str | None = None
    variant: str | None = None

@dataclass
class ImprovementProposal:
    id: str
    agent_id: str
    description: str
    baseline: float
    candidate: float
    status: str
