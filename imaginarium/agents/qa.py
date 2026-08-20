"""Mr. Data: QA and critic agent.

Responsible for independent quality assurance and objective critique of artifacts.
Mr. Data ensures products meet quality standards before publication.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
from pathlib import Path

if TYPE_CHECKING:
    from imaginarium.core.store import Store
    from imaginarium.core.models import Proposal

from imaginarium.agents import BaseAgent
from imaginarium.core.models import Verdict


class MrData(BaseAgent):
    """QA and critic agent.
    
    Responsibilities:
    - Conduct independent quality assurance
    - Provide objective critique of artifacts
    - Ensure products meet quality thresholds
    - Identify completeness, usefulness, truthfulness issues
    """

    MIN_ARTIFACT_SIZE = 800  # Minimum bytes for artifact
    MIN_QUALITY_SCORE = 75   # Minimum model QA score (0-100)

    def __init__(
        self,
        agent_id: str = "data",
        lineage: str = "Mr. Data",
        display_name: str = "Mr. Data",
        role: str = "Critic/QA Agent",
        store: Store = None,
        **kwargs
    ):
        super().__init__(agent_id, lineage, display_name, role, store, **kwargs)

    def execute(self, proposal: Proposal, artifact: Path) -> Verdict:
        """Conduct QA on an artifact.
        
        Args:
            proposal: Original proposal
            artifact: Path to artifact to review
            
        Returns:
            Verdict with approved=True or reasons for rejection
        """
        return self.qa(proposal, artifact)

    def qa(self, proposal: Proposal, artifact: Path) -> Verdict:
        """Perform quality assurance on artifact.
        
        Checks:
        1. Artifact size (must be >800 bytes)
        2. Completeness and usefulness
        3. Truthfulness and originality risk
        4. Instructions clarity
        5. Customer value delivery
        
        Args:
            proposal: Original proposal
            artifact: Path to artifact
            
        Returns:
            Verdict: approved=True if passes all checks
        """
        reasons = []
        
        # Read artifact
        if not artifact.exists():
            reasons.append("artifact file not found")
            verdict = Verdict(False, reasons)
            self.log("qa_review", {
                "proposal_id": proposal.id,
                "approved": False,
                "reasons": reasons,
            })
            return verdict
        
        content = artifact.read_text(encoding="utf-8")
        
        # Check size
        if len(content) < self.MIN_ARTIFACT_SIZE:
            reasons.append(f"artifact too small (min {self.MIN_ARTIFACT_SIZE} bytes)")
        
        # Check for common quality issues
        if "[TODO]" in content or "[PLACEHOLDER]" in content:
            reasons.append("artifact contains placeholder content")
        
        if len(content.split("\n")) < 10:
            reasons.append("artifact lacks sufficient depth")
        
        # TODO: Integrate with Brain for AI-based quality scoring
        # For now, deterministic checks only
        
        verdict = Verdict(not reasons, reasons)
        self.log("qa_review", {
            "proposal_id": proposal.id,
            "artifact_size": len(content),
            "approved": verdict.approved,
            "reasons": verdict.reasons,
        })
        return verdict
