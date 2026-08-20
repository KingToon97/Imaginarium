"""HK-47: Pricing agent.

Responsible for setting fair, ethical prices for products based on
customer value, market conditions, and business strategy.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from imaginarium.core.store import Store
    from imaginarium.core.models import Proposal

from imaginarium.agents import BaseAgent


class HK47(BaseAgent):
    """Pricing agent.
    
    Responsibilities:
    - Set fair and ethical prices
    - Balance customer value with revenue
    - Respect market constraints
    """

    MIN_PRICE_PENCE = 100    # £1.00 minimum
    MAX_PRICE_PENCE = 10000  # £100.00 maximum

    def __init__(
        self,
        agent_id: str = "hk47",
        lineage: str = "HK-47",
        display_name: str = "HK-47",
        role: str = "Pricing Agent",
        store: Store = None,
        **kwargs
    ):
        super().__init__(agent_id, lineage, display_name, role, store, **kwargs)

    def execute(self, proposal: Proposal) -> int:
        """Determine price for a proposal.
        
        Args:
            proposal: Proposal to price
            
        Returns:
            Price in pence (100 = £1.00)
        """
        return self.price(proposal)

    def price(self, proposal: Proposal) -> int:
        """Calculate a fair price for a product.
        
        Pricing strategy:
        1. Start with expected_revenue_pence from proposal
        2. Clamp to MIN/MAX bounds
        3. Adjust based on customer_value
        4. Log decision
        
        Args:
            proposal: Proposal to price
            
        Returns:
            Price in pence
        """
        base_price = proposal.expected_revenue_pence
        
        # Apply value adjustment
        value_factor = max(0.5, proposal.customer_value)  # 50% at min, 100% at max
        adjusted_price = int(base_price * value_factor)
        
        # Clamp to bounds
        price = max(self.MIN_PRICE_PENCE, min(self.MAX_PRICE_PENCE, adjusted_price))
        
        self.log("pricing_decision", {
            "proposal_id": proposal.id,
            "base_price": base_price,
            "value_factor": value_factor,
            "final_price": price,
        })
        return price
