"""Refactored Imaginarium application orchestrator.

Coordinates all agents, enforces Core Laws, manages business pipeline execution.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Optional

from imaginarium.core.laws import verify_core_integrity
from imaginarium.core.store import Store
from imaginarium.core.authority import AuthorityPolicy
from imaginarium.core.hydra import HydraProtocol
from imaginarium.core.morale import MoraleSystem
from imaginarium.core.treasury import TreasuryPolicy
from imaginarium.core.self_improvement import SelfImprovementManager
from imaginarium.core.models import Proposal
from imaginarium.agents import AgentRegistry
from imaginarium.services.pipeline import BusinessPipeline


class Imaginarium:
    """Autonomous multi-agent business engine orchestrator.
    
    Authority hierarchy:
    1. Core Laws (immutable)
    2. Primary Operator (you)
    3. Mr. House (permanent Overseer)
    4. Specialist Agents (Hydra-capable)
    
    This class coordinates all agents, enforces constraints, and manages
    the business pipeline from opportunity discovery through sales.
    """

    def __init__(self, home: Path | str | None = None):
        """Initialize Imaginarium.
        
        Args:
            home: Optional home directory for runtime files. Defaults to ./runtime
        """
        # Core infrastructure
        self.store = Store(home)
        self.authority = AuthorityPolicy(
            primary_name=os.getenv("IMAGINARIUM_PRIMARY_NAME", "Primary Operator")
        )
        
        # Initialize agents via registry
        self.agents = AgentRegistry(self.store)
        
        # Convenience properties for common agents
        self.house = self.agents.get("house")
        self.hal = self.agents.get("hal")
        self.cortana = self.agents.get("cortana")
        self.glados = self.agents.get("glados")
        self.walle = self.agents.get("walle")
        self.data = self.agents.get("data")
        self.hk = self.agents.get("hk47")
        self.r2 = self.agents.get("r2d2")
        self.j5 = self.agents.get("johnny5")
        self.tars = self.agents.get("tars")
        self.k2 = self.agents.get("k2so")
        self.skynet = self.agents.get("skynet")
        
        # Control systems
        self.morale = MoraleSystem(self.store)
        self.treasury = TreasuryPolicy(
            self.store,
            reinvestment_rate=float(os.getenv("IMAGINARIUM_REINVESTMENT_RATE", "0.25"))
        )
        self.hydra = HydraProtocol(self.store, self.authority)
        self.self_improvement = SelfImprovementManager(self.store)
        
        # Business pipeline
        self.pipeline = BusinessPipeline(self)

    def execute(
        self,
        idea: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute a complete business cycle.
        
        Pipeline:
        1. Discover or accept opportunity (HAL)
        2. Score market potential (Cortana)
        3. Review compliance (GLaDOS - hard veto)
        4. Check treasury authorization (K-2SO - hard veto)
        5. Build artifact (WALL-E)
        6. Conduct QA (Mr. Data)
        7. Set price (HK-47)
        8. Publish storefront (R2-D2)
        9. Create marketing copy (Johnny 5)
        10. Log success and award morale
        
        Args:
            idea: Optional pre-formed idea dict. If None, HAL discovers one.
            
        Returns:
            Execution result dict with status and details
        """
        verify_core_integrity()
        return self.pipeline.execute(idea)

    def record_sale(
        self,
        proposal_id: str,
        gross_pence: int,
        fee_pence: int = 0,
        external_id: str | None = None,
    ) -> dict[str, Any]:
        """Record a verified sale transaction.
        
        Args:
            proposal_id: ID of sold product
            gross_pence: Gross transaction amount
            fee_pence: Payment processor fees
            external_id: External transaction ID (e.g., from Stripe)
            
        Returns:
            Sale record
        """
        verify_core_integrity()
        net_pence = max(0, gross_pence - fee_pence)
        self.store.book_revenue(net_pence, f"sale:{proposal_id}")
        self.morale.award(self.tars.agent_id, 10, "verified genuine sale recorded")
        return {
            "status": "recorded",
            "proposal_id": proposal_id,
            "net_pence": net_pence,
        }

    def trigger_hydra(
        self,
        agent_id: str,
        reason: str,
        benchmark_a: float = 0.51,
        benchmark_b: float = 0.52,
    ) -> dict[str, Any]:
        """Manually trigger Hydra protocol on an agent.
        
        Creates two descendants, benchmarks them, and promotes the winner.
        Cannot be applied to Mr. House.
        
        Args:
            agent_id: ID of agent to fail
            reason: Failure reason
            benchmark_a: Score for child A
            benchmark_b: Score for child B
            
        Returns:
            Hydra event details
        """
        verify_core_integrity()
        return self.hydra.trigger(agent_id, reason, benchmark_a, benchmark_b)

    def status(self) -> dict[str, Any]:
        """Get current system status.
        
        Returns:
            Status dict with balance, agents, products, and Hydra roster
        """
        return {
            "balance_pence": self.store.balance(),
            "primary_operator": self.authority.primary_name,
            "authority_precedence": self.authority.precedence(),
            "agents": {
                agent_id: {
                    "display_name": agent.display_name,
                    "role": agent.role,
                    "generation": agent.generation,
                    "status": "active",  # TODO: fetch from store
                }
                for agent_id, agent in self.agents.all().items()
            },
            "morale": self._morale_summary(),
            "treasury": {
                "balance_pence": self.store.balance(),
                "reinvestment_rate": self.treasury.reinvestment_rate,
                "reinvestment_budget_pence": self.treasury.reinvestment_budget(),
            },
        }

    def _morale_summary(self) -> dict[str, int]:
        """Get morale summary for all agents."""
        # TODO: Query store for morale values
        return {}


def demo():
    """Run a demonstration cycle."""
    app = Imaginarium()
    idea = {
        "title": "Freelance Project Budget Template",
        "description": "An original budgeting worksheet guide for freelancers to estimate project costs and margins.",
        "channel": "local storefront",
        "expected_revenue_pence": 500,
        "expected_cost_pence": 0,
        "vulnerability_risk": "low",
        "legal_confidence": 0.98,
        "customer_value": 0.8,
        "probability_of_sale": 0.2,
        "hours_to_launch": 1.0,
    }
    result = app.execute(idea)
    print(json.dumps(result, indent=2, default=str))
    print(f"\nTreasury balance: £{app.store.balance() / 100:.2f}")
    print(f"Status: {json.dumps(app.status(), indent=2, default=str)}")


if __name__ == "__main__":
    demo()
