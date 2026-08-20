"""Cortana: Market analyst agent.

Responsible for analyzing market potential, demand signals, and
revenue/cost/effort tradeoffs for proposed opportunities.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from imaginarium.core.store import Store
    from imaginarium.core.models import Proposal

from imaginarium.agents import BaseAgent


class Cortana(BaseAgent):
    """Market analyst agent.
    
    Responsibilities:
    - Score market potential of proposals
    - Evaluate revenue/cost/effort tradeoffs
    - Provide demand signal analysis
    """

    def __init__(
        self,
        agent_id: str = "cortana",
        lineage: str = "Cortana",
        display_name: str = "Cortana",
        role: str = "Market Analyst",
        store: Store = None,
        **kwargs
    ):
        super().__init__(agent_id, lineage, display_name, role, store, **kwargs)

    def execute(self, proposal: Proposal) -> float:
        """Score market potential of a proposal.
        
        Args:
            proposal: Proposal to analyze
            
        Returns:
            Market score (0.0 to 1.0)
        """
        return self.score(proposal)

    def score(self, proposal: Proposal) -> float:
        """Calculate market potential score.
        
        Score combines:
        - Revenue * probability of sale (demand signal)
        - Customer value (quality signal)
        - Effort (hours to launch)
        
        Args:
            proposal: Proposal to score
            
        Returns:
            Market score (0.0 to 1.0, higher is better)
        """
        revenue = proposal.expected_revenue_pence / 10000  # Normalize
        probability = proposal.probability_of_sale
        value = proposal.customer_value
        effort = max(proposal.hours_to_launch, 0.25)  # Prevent division by zero
        
        score = (revenue * probability * value) / effort
        # Normalize to 0-1 range
        score = min(1.0, score / 10.0)
        
        self.log("market_analysis", {
            "proposal_id": proposal.id,
            "score": score,
            "revenue": revenue,
            "probability": probability,
            "value": value,
            "effort": effort,
        })
        return score
