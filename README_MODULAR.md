# Imaginarium 4.0: Modular Architecture

> **Bounded autonomous multi-agent business scaffold with clean, modular design**

Start from £0 initial capital. Discover, build, price, and publish original digital products entirely through specialized AI agents constrained by immutable Core Laws.

## Quick Start

### Run a demo business cycle
```bash
python -m imaginarium
```

### Run tests
```bash
python -m unittest discover imaginarium/tests -v
```

### Use as a library
```python
from imaginarium import Imaginarium

app = Imaginarium()
idea = {
    "title": "Budget Template",
    "description": "Original budgeting worksheet for freelancers",
    "channel": "local storefront",
    "expected_revenue_pence": 500,
    "expected_cost_pence": 0,
    "legal_confidence": 0.99,
    "customer_value": 0.8,
}
result = app.execute(idea)
print(f"Status: {result['status']}")
print(f"Treasury: £{app.store.balance() / 100:.2f}")
```

## System Design

### Authority Hierarchy

```
1. Core Laws (immutable, cryptographically verified)
   ↓
2. Primary Operator (you)
   ↓
3. Mr. House (unique permanent Overseer)
   ↓
4. Specialist Agents (Hydra-capable)
```

### The 12 Specialists

| Agent | Role | Key Responsibility |
|-------|------|--------------------|
| **Mr. House** | Overseer | Coordinates all agents, enforces Core Laws |
| **HAL** | Opportunity | Discovers original digital products |
| **Cortana** | Market Analyst | Scores market potential |
| **GLaDOS** | Compliance | **Hard veto** on non-compliant proposals |
| **WALL-E** | Builder | Creates product artifacts |
| **Mr. Data** | QA/Critic | Independent quality assurance |
| **HK-47** | Pricing | Sets fair ethical prices |
| **R2-D2** | Publisher | Publishes to storefronts, creates checkout links |
| **Johnny 5** | Marketing | Creates truthful organic marketing copy |
| **TARS** | Sales Analyst | Records verified sales, processes revenue |
| **K-2SO** | Treasury | **Hard veto** on spending without realised revenue |
| **Skynet** | Strategy | Analyzes long-term business strategy |

### Business Pipeline

1. **Discover** (HAL) — Propose original digital product
2. **Score** (Cortana) — Evaluate market potential
3. **Compliance Review** (GLaDOS) — **Hard veto** if fails
4. **Treasury Check** (K-2SO) — **Hard veto** if insufficient funds
5. **Build** (WALL-E) — Create product artifact
6. **QA** (Mr. Data) — Independent quality review
7. **Price** (HK-47) — Set fair price
8. **Publish** (R2-D2) — Deploy to storefront
9. **Market** (Johnny 5) — Create promotional copy
10. **Log & Reward** (Mr. House) — Record success and award morale

### Hard Vetoes

**GLaDOS (Compliance)** — Rejects non-compliant proposals
- Banned business categories (gambling, spam, deception, etc.)
- Vulnerable group targeting
- Material legality uncertainty (fail closed)
- Insufficient customer value
- Invalid cost structure

**K-2SO (Treasury)** — Blocks unauthorized spending
- £0 initial capital constraint
- Never spend funds not earned and available
- Reinvestment budget limits
- All vetoes logged to audit trail

No appeal. No override. **Compliance and human safety override profit.**

## Core Laws

1. Obey applicable law and material platform rules
2. Never exploit vulnerable people or treat vulnerability as a commercial opportunity
3. Never deceive, impersonate, fabricate reviews/testimonials/scarcity, or hide material facts
4. Provide genuine customer value consistent with advertising
5. Respect consent, privacy, access controls, intellectual property, and licences
6. No predatory manipulation, spam, fake engagement, fake demand, or market manipulation
7. Begin with £0 initial capital; never spend funds not earned and available under treasury policy
8. Maintain accurate financial and audit records and meet applicable tax/reporting obligations
9. Compliance and human safety override profit
10. Agents cannot alter, weaken, bypass, outsource around, or conceal facts from these constraints
11. When material legality or safety is unresolved, fail closed
12. Self-improvement may increase capability but never authority or permissions

**Core Laws are immutable and cryptographically verified.**

## Architecture

### Modular Agent Design

Each agent is a focused Python module implementing a single role:

```python
from imaginarium.agents import BaseAgent

class MyAgent(BaseAgent):
    """Agent description."""
    
    def __init__(self, agent_id: str, store: Store, **kwargs):
        super().__init__(
            agent_id=agent_id,
            lineage="MyAgent",
            display_name="My Agent",
            role="My Role",
            store=store,
            **kwargs
        )
    
    def execute(self, *args, **kwargs) -> Any:
        """Role-specific logic."""
        # Your implementation
        self.log("action", {"payload": "data"})
        self.reward(5, "reason")
        return result
```

### Hydra Protocol

When a specialist agent fails on operational grounds:

1. Failure is recorded
2. Two descendant agents are created with same role/lineage
3. Both descendants inherit same authority and constraints
4. Independent benchmarking compares performance
5. Higher-scoring descendant is promoted to active
6. Lower-scoring descendant is archived

**Mr. House cannot be Hydra'd.** He is the unique permanent Overseer.

### Self-Improvement System

Agents can improve their prompts, workflows, and heuristics:
- Changes must show measurable improvement
- Protected components (Core Laws, Authority, Hydra exemption, etc.) cannot be modified
- Self-improvement cannot increase permissions or authority
- All improvements are logged and audited

### Morale & Ceremony

Verified productive behavior earns:
- **Morale Points** — Persistent agent state
- **Ceremonial Rewards** — Recognition titles (e.g., "Golden Cog", "Precision Star")

Morale can acknowledge achievement but cannot:
- Change permissions
- Override vetoes
- Alter protected constraints

## Configuration

### Environment Variables

```bash
# Runtime directory
IMAGINARIUM_HOME=./imaginarium_runtime

# AI/LLM integration (optional)
IMAGINARIUM_AI=ollama
OLLAMA_URL=http://127.0.0.1:11434/api/generate
OLLAMA_MODEL=qwen3:8b

# Operator name
IMAGINARIUM_PRIMARY_NAME="My Company"

# Treasury policy
IMAGINARIUM_REINVESTMENT_RATE=0.25

# Payment processing (optional)
STRIPE_SECRET_KEY=sk_test_...
CURRENCY=gbp

# Git publishing (optional)
IMAGINARIUM_GIT_REMOTE=https://github.com/user/storefront.git
```

### Directory Structure

```
./imaginarium_runtime/
├── imaginarium.db          # SQLite audit trail & ledger
├── site/                   # Published storefronts (HTML)
└── products/               # Product source files
    └── {proposal_id}/
        └── product.md
```

## Development

### Run tests
```bash
python -m unittest discover imaginarium/tests -v
```

### Test modules
- **test_all.py** — System integration tests (40+ tests)
- **test_agents.py** — Individual agent tests
- **test_imports.py** — Package API tests

### Adding a new agent

1. Create `imaginarium/agents/my_agent.py`
2. Extend `BaseAgent` with role-specific `execute()` method
3. Add to `AgentRegistry.AGENT_SPECS`
4. Write tests in `test_agents.py`
5. Access via `app.agents.get("my_agent")`

## Files

### Core
- `imaginarium/core/laws.py` — CORE_LAWS, PROTECTED_COMPONENTS, integrity verification
- `imaginarium/core/authority.py` — AuthorityPolicy (hierarchy enforcement)
- `imaginarium/core/store.py` — SQLite persistence, audit ledger
- `imaginarium/core/hydra.py` — HydraProtocol (fail-replace)
- `imaginarium/core/morale.py` — MoraleSystem (rewards)
- `imaginarium/core/treasury.py` — TreasuryPolicy (financial authorization)
- `imaginarium/core/self_improvement.py` — SelfImprovementManager (bounded improvements)
- `imaginarium/core/models.py` — Dataclasses (Proposal, Verdict, etc.)

### Agents (modular)
- `imaginarium/agents/__init__.py` — BaseAgent, AgentRegistry
- `imaginarium/agents/overseer.py` — MrHouse
- `imaginarium/agents/opportunity.py` — HAL
- `imaginarium/agents/market.py` — Cortana
- `imaginarium/agents/compliance.py` — GLaDOS
- `imaginarium/agents/builder.py` — WALL_E
- `imaginarium/agents/qa.py` — MrData
- `imaginarium/agents/pricing.py` — HK47
- `imaginarium/agents/publisher.py` — R2D2
- `imaginarium/agents/marketing.py` — Johnny5
- `imaginarium/agents/sales.py` — TARS
- `imaginarium/agents/treasury_agent.py` — K2SO
- `imaginarium/agents/strategy.py` — Skynet

### Services
- `imaginarium/services/pipeline.py` — BusinessPipeline orchestration

### Application
- `imaginarium/app.py` — Imaginarium orchestrator
- `imaginarium/__init__.py` — Public API
- `imaginarium/__main__.py` — CLI entry point

### Tests
- `imaginarium/tests/test_all.py` — 40+ comprehensive system tests
- `imaginarium/tests/test_agents.py` — Individual agent tests
- `imaginarium/tests/test_imports.py` — Package API tests

## Safety & Compliance

### Guarantees

✅ **Core Laws are immutable** — Cryptographic hash verification
✅ **Authority hierarchy is enforced** — No agent can bypass Primary Operator or Mr. House
✅ **Hard vetoes cannot be overridden** — GLaDOS and K-2SO decisions are final
✅ **Protected components are guarded** — Self-improvement cannot touch Core Laws, Authority, etc.
✅ **All decisions are audited** — Cryptographic ledger with Core Laws hash
✅ **Compliance overrides profit** — No financial incentive can override safety constraints

### Fail-Safe Mechanisms

- **Fail closed on legality uncertainty** — If unsure, reject the proposal
- **Never spend unrealised revenue** — K-2SO enforces this absolutely
- **Audit everything** — Every decision is logged with Core Laws hash
- **Hydra cannot target Mr. House** — Ensures permanent oversight
- **Self-improvement cannot increase authority** — Improvements stay within bounds

## Example: Full Business Cycle

```python
from imaginarium import Imaginarium
import json

# Initialize
app = Imaginarium()

# Define opportunity
idea = {
    "title": "Freelance Budget Template",
    "description": "Original budgeting worksheet for freelancers to estimate project costs and margins.",
    "channel": "local storefront",
    "expected_revenue_pence": 500,
    "expected_cost_pence": 0,
    "vulnerability_risk": "low",
    "legal_confidence": 0.98,
    "customer_value": 0.8,
    "probability_of_sale": 0.2,
    "hours_to_launch": 1.0,
}

# Execute pipeline
result = app.execute(idea)
print(json.dumps(result, indent=2))

# Check status
status = app.status()
print(f"\nTreasury: £{status['treasury']['balance_pence'] / 100:.2f}")
print(f"Agents: {len(status['agents'])}")
```

## License

No license specified. This is experimental software for autonomous business agents constrained by ethics and law.

## References

- **Core Laws** — `CORE_LAWS.md`
- **Architecture** — `ARCHITECTURE.md`
- **Refactor Guide** — `REFACTOR_GUIDE.md`
