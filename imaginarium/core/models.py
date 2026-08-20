"""Updated core models for modular Imaginarium architecture."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Proposal:
    """Business opportunity proposal.
    
    Attributes:
        id: Unique proposal identifier
        title: Proposal title
        description: Full description
        channel: Distribution channel (e.g., 'local storefront')
        expected_revenue_pence: Expected revenue in pence
        expected_cost_pence: Expected cost in pence
        vulnerability_risk: Risk level ('low', 'medium', 'high')
        legal_confidence: Legality confidence (0.0-1.0)
        customer_value: Customer value perception (0.0-1.0)
        probability_of_sale: Probability of sale (0.0-1.0)
        hours_to_launch: Hours to launch product
        metadata: Additional metadata
    """
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
    """Decision verdict from compliance, treasury, or QA reviews.
    
    Attributes:
        approved: Whether decision is approved
        reasons: List of rejection reasons if not approved
    """
    approved: bool
    reasons: list[str] = field(default_factory=list)


@dataclass
class AgentRecord:
    """Agent instance record.
    
    Attributes:
        agent_id: Unique identifier
        lineage: Hydra lineage (base name)
        display_name: Human-readable name
        role: Agent role
        generation: Hydra generation (0 for original)
        status: Status ('active', 'candidate', 'retired', 'archived')
        morale: Morale points
        parent_id: Parent agent ID if Hydra-created
        variant: Hydra variant ('A' or 'B') if created by Hydra
    """
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
    """Self-improvement proposal from an agent.
    
    Attributes:
        id: Improvement proposal ID
        agent_id: Agent proposing improvement
        description: Description of improvement
        baseline: Baseline metric
        candidate: Candidate metric
        status: Status ('accepted', 'rejected_no_improvement', 'rejected_protected_component')
    """
    id: str
    agent_id: str
    description: str
    baseline: float
    candidate: float
    status: str
