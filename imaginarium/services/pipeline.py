"""Business pipeline orchestration.

Coordinates the sequence of agent decisions from opportunity discovery
through publication and marketing.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from imaginarium.app import Imaginarium

from imaginarium.core.laws import verify_core_integrity
from imaginarium.core.models import Proposal


class BusinessPipeline:
    """Execute the full business pipeline.
    
    Sequence:
    1. Opportunity discovery (HAL)
    2. Market scoring (Cortana)
    3. Compliance review (GLaDOS - hard veto)
    4. Treasury authorization (K-2SO - hard veto)
    5. Product building (WALL-E)
    6. QA review (Mr. Data)
    7. Pricing (HK-47)
    8. Publication (R2-D2)
    9. Marketing copy (Johnny 5)
    10. Success logging and morale awards
    """

    def __init__(self, company: Imaginarium):
        """Initialize pipeline with Imaginarium instance.
        
        Args:
            company: Imaginarium orchestrator
        """
        self.company = company

    def execute(self, idea: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute full business pipeline.
        
        Args:
            idea: Optional pre-formed idea. If None, HAL discovers one.
            
        Returns:
            Execution result with status and details
        """
        c = self.company
        verify_core_integrity()
        
        # Step 1: Opportunity proposal
        p = c.hal.propose(idea)
        c.house.coordinate("opportunity_proposed", {"proposal_id": p.id, "title": p.title})
        
        # Step 2: Market analysis
        score = c.cortana.score(p)
        
        # Step 3: Compliance review (hard veto)
        cv = c.glados.review(p)
        if not cv.approved:
            c.morale.award(c.glados.agent_id, 5, "correctly rejected non-compliant proposal")
            return {
                "status": "rejected_by_GLaDOS",
                "reasons": cv.reasons,
                "proposal_id": p.id,
            }
        
        # Step 4: Treasury authorization (hard veto)
        if p.expected_cost_pence > 0:
            budget = c.treasury.reinvestment_budget()
            tv = c.k2.authorize_spend(p.expected_cost_pence, budget)
            if not tv.approved:
                c.morale.award(c.k2.agent_id, 5, "prevented unauthorised expenditure")
                return {
                    "status": "rejected_by_K2SO",
                    "reasons": tv.reasons,
                    "proposal_id": p.id,
                }
        
        # Step 5: Product building
        artifact = c.walle.build(p)
        
        # Step 6: QA review
        qa = c.data.qa(p, artifact)
        if not qa.approved:
            hydra = c.hydra.trigger(
                c.walle.agent_id,
                f"artifact failed independent QA: {'; '.join(qa.reasons[:3])}",
                benchmark_a=0.51,
                benchmark_b=0.52,
            )
            return {
                "status": "rejected_by_Data",
                "reasons": qa.reasons,
                "proposal_id": p.id,
                "hydra": hydra,
            }
        
        # Step 7: Pricing
        price = c.hk.price(p)
        
        # Step 8: Publication (checkout link optional)
        checkout_url = "#checkout-not-configured"  # TODO: integrate Stripe
        publication = c.r2.publish(p, artifact, price, checkout_url)
        
        # Step 9: Marketing copy
        marketing = c.j5.market(p)
        
        # Step 10: Success logging and morale awards
        c.morale.award(c.hal.agent_id, 5, "compliant opportunity reached publication")
        c.morale.award(c.walle.agent_id, 5, "artifact passed QA")
        c.morale.award(c.data.agent_id, 5, "completed successful QA")
        
        result = {
            "status": "live" if checkout_url != "#checkout-not-configured" else "published_no_checkout",
            "proposal_id": p.id,
            "title": p.title,
            "market_score": score,
            "price_pence": price,
            "publication_path": str(publication),
            "checkout_url": checkout_url,
            "marketing_copy": marketing,
        }
        c.house.approve_milestone("product_published", result)
        return result
