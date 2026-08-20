"""HAL: Opportunity discovery agent.

Responsible for discovering and proposing original digital products
and small software utilities that can be created with zero upfront spending.
"""
from __future__ import annotations
import json
import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from imaginarium.core.store import Store

from imaginarium.agents import BaseAgent
from imaginarium.core.models import Proposal


class HAL(BaseAgent):
    """Opportunity discovery agent.
    
    Responsibilities:
    - Discover original digital products and utilities
    - Propose ideas for business execution
    - Ensure ideas comply with basic feasibility constraints
    """

    def __init__(
        self,
        agent_id: str = "hal",
        lineage: str = "HAL",
        display_name: str = "HAL",
        role: str = "Opportunity Agent",
        store: Store = None,
        **kwargs
    ):
        super().__init__(agent_id, lineage, display_name, role, store, **kwargs)

    def execute(self, idea: dict[str, Any]) -> Proposal:
        """Not used; use propose() instead."""
        raise NotImplementedError("Use propose() to generate opportunities.")

    def propose(self, idea: dict[str, Any] = None) -> Proposal:
        """Propose an opportunity.
        
        Args:
            idea: Optional pre-formed idea dict. If None, generates one from AI.
            
        Returns:
            Proposal object ready for review.
        """
        if idea:
            # Validate and enrich provided idea
            idea_id = idea.get("id") or str(uuid.uuid4())
            p = Proposal(
                id=idea_id,
                title=idea.get("title", "Untitled"),
                description=idea.get("description", ""),
                channel=idea.get("channel", "local"),
                expected_revenue_pence=int(idea.get("expected_revenue_pence", 0)),
                expected_cost_pence=int(idea.get("expected_cost_pence", 0)),
                vulnerability_risk=idea.get("vulnerability_risk", "low"),
                legal_confidence=float(idea.get("legal_confidence", 0.95)),
                customer_value=float(idea.get("customer_value", 0.6)),
                probability_of_sale=float(idea.get("probability_of_sale", 0.1)),
                hours_to_launch=float(idea.get("hours_to_launch", 1.0)),
            )
            self.log("opportunity_proposed", {"proposal_id": p.id, "title": p.title})
            return p
        else:
            # Generate from AI (requires Brain integration)
            # TODO: Integrate with Brain for autonomous discovery
            raise NotImplementedError(
                "AI-generated opportunities require Brain integration."
            )
