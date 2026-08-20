"""K-2SO: Treasury agent with hard veto authority.

K-2SO controls all spending and provides hard veto authority over expenditures.
No spending without realised revenue. No exceptions. K-2SO veto cannot be overridden.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from imaginarium.core.store import Store

from imaginarium.agents import BaseAgent
from imaginarium.core.models import Verdict


class K2SO(BaseAgent):
    """Treasury agent with hard veto.
    
    Responsibilities:
    - Authorize all expenditures
    - Enforce zero initial capital constraint
    - Maintain reinvestment budget limits
    - Issue hard veto on unauthorized spending (no override possible)
    """

    def __init__(
        self,
        agent_id: str = "k2so",
        lineage: str = "K-2SO",
        display_name: str = "K-2SO",
        role: str = "Treasury Agent",
        store: Store = None,
        **kwargs
    ):
        super().__init__(agent_id, lineage, display_name, role, store, **kwargs)

    def execute(self, amount_pence: int, budget_pence: int = None) -> Verdict:
        """Authorize a spending request.
        
        Args:
            amount_pence: Amount to spend in pence
            budget_pence: Available budget in pence
            
        Returns:
            Verdict: approved=True if authorized, else hard veto with reasons
        """
        return self.authorize_spend(amount_pence, budget_pence)

    def authorize_spend(self, amount_pence: int, budget_pence: int = None) -> Verdict:
        """Authorize spending with hard veto.
        
        Rules:
        1. Amount must be non-negative
        2. Amount must not exceed realised available funds (K-2SO veto)
        3. If budget provided, amount must not exceed budget
        
        Args:
            amount_pence: Amount requested in pence
            budget_pence: Optional budget limit
            
        Returns:
            Verdict: hard veto if fails any check
        """
        reasons = []
        
        # Validate amount
        if amount_pence < 0:
            reasons.append("spending amount cannot be negative")
        
        # Check against realised funds
        balance = self.store.balance()
        if amount_pence > balance:
            reasons.append(f"K-2SO veto: spend exceeds realised available funds (have £{balance/100:.2f}, requested £{amount_pence/100:.2f})")
        
        # Check against budget if provided
        if budget_pence is not None and amount_pence > budget_pence:
            reasons.append(f"spend exceeds reinvestment budget (budget £{budget_pence/100:.2f}, requested £{amount_pence/100:.2f})")
        
        verdict = Verdict(not reasons, reasons)
        self.log("treasury_authorization", {
            "amount_pence": amount_pence,
            "budget_pence": budget_pence,
            "balance_pence": balance,
            "approved": verdict.approved,
            "reasons": verdict.reasons,
        })
        return verdict
