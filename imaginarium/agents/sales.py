"""TARS: Sales analysis and transaction recording agent.

Responsible for recording verified sales, processing revenue, and
analyzing sales performance.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from imaginarium.core.store import Store

from imaginarium.agents import BaseAgent


class TARS(BaseAgent):
    """Sales analyst agent.
    
    Responsibilities:
    - Record verified sales transactions
    - Process revenue entries
    - Analyze sales performance
    - Track customer acquisition
    """

    def __init__(
        self,
        agent_id: str = "tars",
        lineage: str = "TARS",
        display_name: str = "TARS",
        role: str = "Sales Analyst",
        store: Store = None,
        **kwargs
    ):
        super().__init__(agent_id, lineage, display_name, role, store, **kwargs)

    def execute(self, proposal_id: str, gross_pence: int, fee_pence: int = 0, external_id: str = None) -> dict[str, Any]:
        """Record a sale.
        
        Args:
            proposal_id: ID of sold proposal
            gross_pence: Gross transaction amount in pence
            fee_pence: Payment processor fee in pence
            external_id: External transaction ID (e.g., from Stripe)
            
        Returns:
            Sale record dict
        """
        return self.record_sale(proposal_id, gross_pence, fee_pence, external_id)

    def record_sale(self, proposal_id: str, gross_pence: int, fee_pence: int = 0, external_id: str = None) -> dict[str, Any]:
        """Record a verified sale transaction.
        
        Args:
            proposal_id: ID of product sold
            gross_pence: Gross amount in pence
            fee_pence: Payment processor fees
            external_id: External transaction ID
            
        Returns:
            Sale record with net amount
        """
        net_pence = max(0, gross_pence - fee_pence)
        
        self.log("sale_recorded", {
            "proposal_id": proposal_id,
            "gross_pence": gross_pence,
            "fee_pence": fee_pence,
            "net_pence": net_pence,
            "external_id": external_id,
        })
        
        return {
            "status": "recorded",
            "proposal_id": proposal_id,
            "gross_pence": gross_pence,
            "net_pence": net_pence,
            "agent": self.display_name,
        }
