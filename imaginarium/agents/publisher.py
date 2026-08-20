"""R2-D2: Publisher agent.

Responsible for publishing products to storefronts, creating checkout links,
and managing payment integrations.
"""
from __future__ import annotations
import re
import html
from typing import TYPE_CHECKING, Any
from pathlib import Path

if TYPE_CHECKING:
    from imaginarium.core.store import Store
    from imaginarium.core.models import Proposal

from imaginarium.agents import BaseAgent


class R2D2(BaseAgent):
    """Publisher agent.
    
    Responsibilities:
    - Publish products to storefronts
    - Generate product landing pages
    - Create checkout links (Stripe integration optional)
    - Manage git-based deployment
    """

    def __init__(
        self,
        agent_id: str = "r2d2",
        lineage: str = "R2-D2",
        display_name: str = "R2-D2",
        role: str = "Publisher Agent",
        store: Store = None,
        **kwargs
    ):
        super().__init__(agent_id, lineage, display_name, role, store, **kwargs)

    def execute(self, proposal: Proposal, artifact: Path, price_pence: int, checkout_url: str = None) -> Path:
        """Publish a product.
        
        Args:
            proposal: Proposal details
            artifact: Product artifact path
            price_pence: Price in pence
            checkout_url: Optional checkout URL
            
        Returns:
            Path to published landing page
        """
        return self.publish(proposal, artifact, price_pence, checkout_url)

    def publish(self, proposal: Proposal, artifact: Path, price_pence: int, checkout_url: str = None) -> Path:
        """Publish product to storefront.
        
        Creates an HTML landing page with product details, pricing, and checkout link.
        
        Args:
            proposal: Proposal details
            artifact: Product artifact file
            price_pence: Price in pence
            checkout_url: Optional checkout link (Stripe Payment Link)
            
        Returns:
            Path to published HTML page
        """
        # Create slug from title
        slug = re.sub(r"[^a-z0-9]+", "-", proposal.title.lower()).strip("-")[:80] or proposal.id
        
        site_dir = self.store.root / "site"
        product_dir = site_dir / slug
        product_dir.mkdir(parents=True, exist_ok=True)
        
        # Read artifact content
        artifact_content = artifact.read_text(encoding="utf-8") if artifact.exists() else "[Product content]"
        
        # Escape HTML
        title_escaped = html.escape(proposal.title)
        desc_escaped = html.escape(proposal.description)
        price_gbp = price_pence / 100
        
        # Generate checkout button
        if checkout_url and checkout_url != "#checkout-not-configured":
            buy_button = f'<a class="buy" href="{html.escape(checkout_url)}">Buy — £{price_gbp:.2f}</a>'
        else:
            buy_button = '<p class="note">Checkout not configured.</p>'
        
        # Build HTML page
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title_escaped} — Imaginarium</title>
    <meta name="description" content="{desc_escaped}">
    <style>
        body {{
            max-width: 820px;
            margin: 60px auto;
            padding: 20px;
            font: 18px/1.6 system-ui, sans-serif;
        }}
        h1 {{ line-height: 1.1; }}
        .buy {{
            display: inline-block;
            padding: 14px 22px;
            background: #111;
            color: #fff;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
        }}
        .buy:hover {{ background: #333; }}
        .note {{ color: #666; }}
    </style>
</head>
<body>
    <p>IMAGINARIUM</p>
    <h1>{title_escaped}</h1>
    <p>{desc_escaped}</p>
    <p><strong>£{price_gbp:.2f}</strong></p>
    {buy_button}
    <hr>
    <div class="content">
        {html.escape(artifact_content)}
    </div>
</body>
</html>"""
        
        # Write page
        page_path = product_dir / "index.html"
        page_path.write_text(html_content, encoding="utf-8")
        
        self.log("published", {
            "proposal_id": proposal.id,
            "page_path": str(page_path),
            "checkout_url": checkout_url or "none",
        })
        return page_path
