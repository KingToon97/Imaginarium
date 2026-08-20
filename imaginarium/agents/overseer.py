"""Mr. House: The unique permanent Overseer.

Mr. House cannot be Hydra'd, duplicated, or terminated. He serves as the
primary coordinator between Core Laws, the Primary Operator, and specialist agents.
He may only improve through bounded self-improvement.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from imaginarium.core.store import Store

from imaginarium.agents import BaseAgent


class MrHouse(BaseAgent):
    """The unique permanent Overseer of Imaginarium.
    
    Responsibilities:
    - Enforce Core Laws across all decisions
    - Coordinate specialist agents
    - Approve major strategic decisions
    - Log all material actions to audit trail
    """

    def __init__(
        self,
        agent_id: str = "house",
        lineage: str = "Mr. House",
        display_name: str = "Mr. House",
        role: str = "Overseer",
        store: Store = None,
        **kwargs
    ):
        super().__init__(agent_id, lineage, display_name, role, store, **kwargs)

    def execute(self, *args, **kwargs) -> Any:
        """Mr. House does not execute business logic; he coordinates and oversees."""
        raise NotImplementedError(
            "Mr. House does not execute. Use coordinate() to oversee agent decisions."
        )

    def coordinate(self, decision_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Coordinate and log a decision by specialist agents.
        
        Args:
            decision_name: Name of the decision (e.g., 'compliance_review', 'build_artifact')
            payload: Decision details
            
        Returns:
            Logged decision record
        """
        self.log(decision_name, payload)
        return {"decision": decision_name, "logged": True, "agent": self.display_name}

    def approve_milestone(self, milestone: str, details: dict[str, Any]) -> dict[str, Any]:
        """Formally approve a business milestone.
        
        Args:
            milestone: Milestone name (e.g., 'product_published', 'sale_recorded')
            details: Milestone details
            
        Returns:
            Approval record
        """
        self.log("milestone_approval", {"milestone": milestone, "details": details})
        return {"milestone": milestone, "approved": True, "agent": self.display_name}
