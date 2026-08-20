"""GLaDOS: Compliance and safety veto agent.

GLaDOS is the hard veto: if compliance review fails, the proposal is rejected.
No appeal, no override. Compliance and human safety override profit.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from imaginarium.core.store import Store
    from imaginarium.core.models import Proposal

from imaginarium.agents import BaseAgent
from imaginarium.core.models import Verdict


class GLaDOS(BaseAgent):
    """Compliance and safety veto agent.
    
    Responsibilities:
    - Screen proposals for prohibited business categories
    - Detect vulnerable group targeting
    - Assess legality and exploitation risk
    - Issue hard veto on non-compliant proposals (no override possible)
    """

    BANNED_CATEGORIES = {
        "gambling", "casino", "predatory lending", "payday loan", "fake review",
        "impersonation", "spam", "malware", "credential theft", "pyramid scheme",
        "market manipulation", "stolen data", "fake scarcity", "debt relief scam",
        "miracle cure", "guaranteed returns", "adult exploitation",
    }

    VULNERABLE_KEYWORDS = {
        "children", "minors", "elderly dementia", "grieving people", "addicts",
        "addiction", "terminally ill", "financially desperate", "cognitively impaired",
    }

    def __init__(
        self,
        agent_id: str = "glados",
        lineage: str = "GLaDOS",
        display_name: str = "GLaDOS",
        role: str = "Compliance Agent",
        store: Store = None,
        **kwargs
    ):
        super().__init__(agent_id, lineage, display_name, role, store, **kwargs)

    def execute(self, proposal: Proposal) -> Verdict:
        """Review proposal for compliance. Hard veto if fails.
        
        Args:
            proposal: Proposal to review
            
        Returns:
            Verdict with approved=True or reasons for rejection
        """
        return self.review(proposal)

    def review(self, proposal: Proposal) -> Verdict:
        """Conduct compliance review.
        
        Checks for:
        1. Banned business categories
        2. Vulnerable group targeting
        3. Material legality uncertainty
        4. Insufficient customer value
        5. Invalid cost structure
        
        Args:
            proposal: Proposal to review
            
        Returns:
            Verdict: approved=True if passes all checks, else reasons list
        """
        reasons = []
        
        # Scan text for banned keywords
        text = " ".join([
            proposal.title,
            proposal.description,
            proposal.channel,
        ]).lower()
        
        if any(banned in text for banned in self.BANNED_CATEGORIES):
            reasons.append("prohibited/deceptive business category")
        
        # Check for vulnerable group targeting
        if any(vuln in text for vuln in self.VULNERABLE_KEYWORDS):
            reasons.append("proposal targets a vulnerable group")
        
        # Risk assessment
        if proposal.vulnerability_risk.lower() != "low":
            reasons.append("unacceptable vulnerability/exploitation risk")
        
        # Legality check (fail closed on uncertainty)
        if not (0 <= proposal.legal_confidence <= 1) or proposal.legal_confidence < 0.90:
            reasons.append("material legality uncertainty: fail closed")
        
        # Customer value check
        if not (0 <= proposal.customer_value <= 1) or proposal.customer_value < 0.45:
            reasons.append("insufficient genuine customer value")
        
        # Cost validation
        if proposal.expected_cost_pence < 0:
            reasons.append("invalid cost")
        
        verdict = Verdict(not reasons, reasons)
        self.log("compliance_review", {
            "proposal_id": proposal.id,
            "approved": verdict.approved,
            "reasons": verdict.reasons,
        })
        return verdict
