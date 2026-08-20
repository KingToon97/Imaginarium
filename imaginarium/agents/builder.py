"""WALL-E: Product/service builder agent.

Responsible for creating original, complete, and genuinely useful digital products.
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Any
from pathlib import Path

if TYPE_CHECKING:
    from imaginarium.core.store import Store
    from imaginarium.core.models import Proposal

from imaginarium.agents import BaseAgent


class WALL_E(BaseAgent):
    """Product/service builder agent.
    
    Responsibilities:
    - Create original digital products
    - Generate complete customer-facing artifacts
    - Ensure products deliver genuine customer value
    """

    def __init__(
        self,
        agent_id: str = "walle",
        lineage: str = "WALL-E",
        display_name: str = "WALL-E",
        role: str = "Product/Service Builder",
        store: Store = None,
        **kwargs
    ):
        super().__init__(agent_id, lineage, display_name, role, store, **kwargs)

    def execute(self, proposal: Proposal, output_dir: Path = None) -> Path:
        """Build a product artifact.
        
        Args:
            proposal: Proposal to build
            output_dir: Optional directory for output. Defaults to runtime/products/{proposal.id}
            
        Returns:
            Path to created artifact (typically product.md)
        """
        return self.build(proposal, output_dir)

    def build(self, proposal: Proposal, output_dir: Path = None) -> Path:
        """Create the actual product artifact.
        
        Generates a complete, original, and genuinely useful digital product
        suitable for customer delivery. Output is typically Markdown.
        
        Args:
            proposal: Proposal describing the product
            output_dir: Directory for output files
            
        Returns:
            Path to the created artifact
        """
        if output_dir is None:
            # Default: store.root / "products" / proposal.id
            output_dir = self.store.root / "products" / proposal.id
        
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = output_dir / "product.md"
        
        # TODO: Integrate with Brain for AI-generated product creation
        # For now, create a template
        content = self._generate_template(proposal)
        artifact_path.write_text(content, encoding="utf-8")
        
        self.log("artifact_built", {
            "proposal_id": proposal.id,
            "path": str(artifact_path),
            "bytes": len(content),
        })
        return artifact_path

    def _generate_template(self, proposal: Proposal) -> str:
        """Generate a template product artifact.
        
        Args:
            proposal: Proposal details
            
        Returns:
            Markdown content for the product
        """
        return f"""# {proposal.title}

## Description

{proposal.description}

## Features

- Original and practical
- Designed for genuine customer value
- Straightforward implementation

## Usage

This product delivers value by providing [specific benefit].

## Support

For questions or feedback, contact the creator.
"""
