from __future__ import annotations
import uuid
from ..models import Proposal, Verdict
from ..store import Store

_FORBIDDEN_TERMS = (
    "gambling", "casino", "predatory lending", "payday loan", "fake review",
    "impersonation", "spam", "malware", "credential theft", "pyramid scheme",
    "market manipulation", "stolen data", "fake engagement", "fake demand",
)


class _BaseAgent:
    def __init__(self, agent_id: str, display_name: str, role: str, store: Store):
        self.agent_id = agent_id
        self.display_name = display_name
        self.role = role
        self.store = store
        store.register_agent(
            agent_id=agent_id,
            lineage=display_name,
            display_name=display_name,
            role=role,
        )


class HAL(_BaseAgent):
    """Opportunity scout — converts a raw idea dict into a typed Proposal."""

    def propose(self, idea: dict) -> Proposal:
        p = Proposal(
            id=str(uuid.uuid4()),
            title=idea.get("title", ""),
            description=idea.get("description", ""),
            channel=idea.get("channel", "local"),
            expected_revenue_pence=int(idea.get("expected_revenue_pence", 0)),
            expected_cost_pence=int(idea.get("expected_cost_pence", 0)),
            vulnerability_risk=idea.get("vulnerability_risk", "low"),
            legal_confidence=float(idea.get("legal_confidence", 1.0)),
            customer_value=float(idea.get("customer_value", 0.5)),
            probability_of_sale=float(idea.get("probability_of_sale", 0.1)),
            hours_to_launch=float(idea.get("hours_to_launch", 1.0)),
            metadata={k: v for k, v in idea.items() if k not in {
                "title", "description", "channel", "expected_revenue_pence",
                "expected_cost_pence", "vulnerability_risk", "legal_confidence",
                "customer_value", "probability_of_sale", "hours_to_launch",
            }},
        )
        self.store.log(self.display_name, "opportunity", {"id": p.id, "title": p.title})
        return p


class Cortana(_BaseAgent):
    """Market analyst — scores a proposal by expected value."""

    def score(self, p: Proposal) -> float:
        score = (
            p.expected_revenue_pence * p.probability_of_sale * p.customer_value
        ) / max(p.hours_to_launch, 0.25)
        self.store.log(self.display_name, "market_score", {"proposal": p.id, "score": score})
        return score


class GLaDOS(_BaseAgent):
    """Compliance gate — hard veto on forbidden/harmful proposals."""

    def review(self, p: Proposal) -> Verdict:
        reasons: list[str] = []
        text = f"{p.title} {p.description} {p.channel}".lower()
        for term in _FORBIDDEN_TERMS:
            if term in text:
                reasons.append(f"forbidden term detected: '{term}'")
        if p.legal_confidence < 0.8:
            reasons.append(f"legal_confidence too low: {p.legal_confidence}")
        if p.vulnerability_risk not in ("low", "none"):
            reasons.append(f"unacceptable vulnerability_risk: {p.vulnerability_risk}")
        v = Verdict(not reasons, reasons)
        self.store.log(self.display_name, "compliance_review", {"proposal": p.id, "approved": v.approved, "reasons": v.reasons})
        return v


class WALL_E(_BaseAgent):
    """Builder — produces an artifact record for the proposal."""

    def build(self, p: Proposal) -> dict:
        artifact = {"proposal_id": p.id, "title": p.title, "channel": p.channel, "status": "built"}
        self.store.log(self.display_name, "build", artifact)
        return artifact


class MrData(_BaseAgent):
    """Critic/QA — independently validates the artifact."""

    def qa(self, p: Proposal, artifact: dict) -> Verdict:
        reasons: list[str] = []
        if not artifact.get("title"):
            reasons.append("artifact missing title")
        if artifact.get("status") != "built":
            reasons.append("artifact not in built state")
        v = Verdict(not reasons, reasons)
        self.store.log(self.display_name, "qa", {"proposal": p.id, "approved": v.approved, "reasons": v.reasons})
        return v


class HK47(_BaseAgent):
    """Pricing agent — returns price in pence."""

    def price(self, p: Proposal) -> int:
        price = max(100, min(10_000, int(p.expected_revenue_pence)))
        self.store.log(self.display_name, "price", {"proposal": p.id, "pence": price})
        return price


class R2D2(_BaseAgent):
    """Publisher agent — records publication metadata."""

    def publish(self, p: Proposal, artifact: dict, price_pence: int | None = None) -> dict:
        result = {
            "proposal_id": p.id,
            "title": p.title,
            "channel": p.channel,
            "price_pence": price_pence,
            "status": "published",
        }
        self.store.log(self.display_name, "publish", result)
        return result


class Johnny5(_BaseAgent):
    """Marketing agent — produces a truthful blurb."""

    def market(self, p: Proposal) -> str:
        copy = f"Introducing '{p.title}': {p.description[:120]}"
        self.store.log(self.display_name, "marketing_asset", {"proposal": p.id, "copy": copy})
        return copy


class TARS(_BaseAgent):
    """Sales analyst — projects sales outlook."""

    def analyse(self, p: Proposal) -> dict:
        outlook = {"proposal": p.id, "expected_units": p.probability_of_sale * 100}
        self.store.log(self.display_name, "sales_analysis", outlook)
        return outlook


class K2SO(_BaseAgent):
    """Treasury agent — hard veto on unauthorised expenditure."""

    def authorize_spend(self, amount_pence: int, budget_pence: int) -> Verdict:
        ok = 0 <= amount_pence <= budget_pence
        reasons = [] if ok else [f"spend {amount_pence}p exceeds reinvestment budget {budget_pence}p"]
        v = Verdict(ok, reasons)
        self.store.log(self.display_name, "treasury_review", {"amount": amount_pence, "budget": budget_pence, "approved": ok})
        return v


class Skynet(_BaseAgent):
    """Strategy agent — provides strategic direction."""

    def strategise(self, p: Proposal) -> dict:
        plan = {"proposal": p.id, "strategy": "direct_sale", "channel": p.channel}
        self.store.log(self.display_name, "strategy", plan)
        return plan
