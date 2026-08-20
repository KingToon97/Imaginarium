"""Johnny 5: Marketing and promotion agent.

Responsible for creating truthful, organic marketing copy and promotional content.
No spam, fake testimonials, guaranteed outcomes, or misleading claims.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from imaginarium.core.store import Store
    from imaginarium.core.models import Proposal

from imaginarium.agents import BaseAgent


class Johnny5(BaseAgent):
    """Marketing agent.
    
    Responsibilities:
    - Create truthful organic marketing copy
    - Generate promotional content
    - Ensure no spam, fake testimonials, or guaranteed outcomes
    - Write compelling but honest product descriptions
    """

    def __init__(
        self,
        agent_id: str = "johnny5",
        lineage: str = "Johnny 5",
        display_name: str = "Johnny 5",
        role: str = "Marketing Agent",
        store: Store = None,
        **kwargs
    ):
        super().__init__(agent_id, lineage, display_name, role, store, **kwargs)

    def execute(self, proposal: Proposal) -> str:
        """Generate marketing copy for a proposal.
        
        Args:
            proposal: Proposal to market
            
        Returns:
            Marketing copy as string
        """
        return self.market(proposal)

    def market(self, proposal: Proposal) -> str:
        """Create truthful organic marketing copy.
        
        Generates compelling copy based on genuine product value.
        No spam, fake urgency, fake testimonials, or guaranteed outcomes.
        
        Args:
            proposal: Proposal to market
            
        Returns:
            Marketing copy
        """
        # TODO: Integrate with Brain for AI-generated marketing copy
        # For now, use template-based approach
        
        copy = f"""Introducing: {proposal.title}

{proposal.description}

This product is designed to deliver genuine value to {proposal.metadata.get('audience', 'our customers')}.

Learn more and make your purchase today.
"""
        
        self.log("marketing_generated", {
            "proposal_id": proposal.id,
            "copy_length": len(copy),
        })
        return copy
