# Imaginarium Refactor: Modular Architecture

This document describes the new modular architecture introduced in the refactor branch.

## What Changed

The codebase has been restructured from a monolithic design to a clean, modular architecture that makes it easy to:

- Add or modify agents without editing the main app
- Test individual components in isolation
- Understand agent responsibilities and constraints
- Extend the system with new capabilities

## New Structure

```
imaginarum/
├── __init__.py                 # Public API exports
├── __main__.py                 # Entry point
├── app.py                      # Main Imaginarium orchestrator
│
├── agents/                     # Modular specialist agents
│   ├── __init__.py            # BaseAgent, AgentRegistry
│   ├── overseer.py            # Mr. House (unique, permanent)
│   ├── opportunity.py         # HAL (Opportunity discovery)
│   ├── market.py              # Cortana (Market analysis)
│   ├── compliance.py          # GLaDOS (Compliance veto)
│   ├── builder.py             # WALL-E (Product builder)
│   ├── qa.py                  # Mr. Data (QA/Critic)
│   ├── pricing.py             # HK-47 (Pricing)
│   ├── publisher.py           # R2-D2 (Publisher)
│   ├── marketing.py           # Johnny 5 (Marketing)
│   ├── sales.py               # TARS (Sales analyst)
│   ├── treasury_agent.py      # K-2SO (Treasury veto)
│   └── strategy.py            # Skynet (Strategy)
│
├── core/                       # Immutable constraints & infrastructure
│   ├── laws.py                # CORE_LAWS, integrity checking
│   ├── authority.py           # Authority hierarchy enforcement
│   ├── store.py               # SQLite persistence layer
│   ├── hydra.py               # Fail-replace protocol
│   ├── morale.py              # Reward & morale system
│   ├── treasury.py            # Financial authorization policy
│   ├── self_improvement.py    # Bounded self-improvement with guards
│   └── models.py              # Dataclasses (Proposal, Verdict, etc.)
│
├── services/
│   └── pipeline.py            # BusinessPipeline orchestrator
│
└── tests/
    ├── test_all.py            # Comprehensive system tests
    ├── test_agents.py         # Individual agent tests
    └── test_imports.py        # Package import tests
```

## Key Improvements

### 1. Agent Registry & Factory Pattern

**Before:** Hard-coded agent instantiation in `app.py`:
```python
self.hal = HAL("hal", "HAL", "Opportunity Agent", self.store)
self.cortana = Cortana("cortana", "Cortana", "Market Analyst", self.store)
# ... 10 more agents
```

**After:** Declarative agent registry:
```python
class AgentRegistry:
    AGENT_SPECS = {
        "hal": {"lineage": "HAL", "role": "Opportunity Agent", "class": "HAL"},
        "cortana": {"lineage": "Cortana", "role": "Market Analyst", "class": "Cortana"},
        # ...
    }
    
    def __init__(self, store: Store):
        self._agents = {}
        self._initialize_all()
```

**Benefits:**
- Adding/removing agents requires only updating `AGENT_SPECS`
- No repeated boilerplate
- Registry handles Hydra descendant creation uniformly

### 2. BaseAgent Abstract Class

All agents now inherit from `BaseAgent` with common lifecycle:

```python
class BaseAgent(ABC):
    def __init__(self, agent_id: str, lineage: str, display_name: str, role: str, store: Store, ...):
        self.agent_id = agent_id
        self.lineage = lineage  # For Hydra lineage tracking
        self.display_name = display_name
        self.role = role
        self.store = store
        self._register()
    
    def log(self, action: str, payload: Any) -> None:
        """Log to audit trail"""
        self.store.log(self.display_name, action, payload)
    
    def reward(self, points: int, reason: str, ceremony: str = "") -> None:
        """Earn morale points"""
        self.store.reward(self.agent_id, points, reason, ceremony)
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Role-specific logic (implemented by subclasses)"""
        pass
```

**Benefits:**
- Consistent logging, rewarding, and lifecycle
- Easy to add new agents (just extend BaseAgent and implement `execute()`)
- Clear interface contract

### 3. Individual Agent Modules

Each agent is now a focused module with clear responsibilities:

**HAL (Opportunity)**
```python
class HAL(BaseAgent):
    def propose(self, idea: dict = None) -> Proposal:
        # Discover or accept ideas
```

**GLaDOS (Compliance - Hard Veto)**
```python
class GLaDOS(BaseAgent):
    def review(self, proposal: Proposal) -> Verdict:
        # Check: banned categories, vulnerable groups, legality, customer value
        # Hard veto: no override possible
```

**K-2SO (Treasury - Hard Veto)**
```python
class K2SO(BaseAgent):
    def authorize_spend(self, amount_pence: int, budget_pence: int = None) -> Verdict:
        # Hard veto: cannot spend unrealised revenue
```

And so on for all 12 agents.

**Benefits:**
- Single responsibility: each module does one thing well
- Easy to understand and maintain
- Easy to test in isolation
- Easy to extend (e.g., add AI integration to a specific agent)

### 4. Comprehensive Test Suite

Three test modules cover different aspects:

**test_all.py** — System integration tests:
- Core law integrity
- Agent registry initialization
- Authority hierarchy
- Compliance veto mechanism
- Treasury veto mechanism
- Full pipeline execution
- Hydra protocol
- Self-improvement guards
- Morale system
- Status reporting

**test_agents.py** — Individual agent tests:
- HAL: idea proposal
- Cortana: market scoring
- GLaDOS: compliance review
- WALL-E: artifact building
- Mr. Data: QA evaluation
- HK-47: pricing
- K-2SO: treasury authorization

**test_imports.py** — Package-level API tests

**Running tests:**
```bash
python -m unittest discover imaginarium/tests -v
```

### 5. Cleaner App Initialization

**Before:**
```python
class Imaginarium:
    def __init__(self, home=None):
        self.store = Store(home)
        self.hal = HAL("hal", "HAL", "Opportunity Agent", self.store)
        self.cortana = Cortana("cortana", "Cortana", "Market Analyst", self.store)
        # ... 10 more manual instantiations
```

**After:**
```python
class Imaginarium:
    def __init__(self, home: Path | str | None = None):
        self.store = Store(home)
        self.authority = AuthorityPolicy(...)
        self.agents = AgentRegistry(self.store)  # Initialize all agents at once
        
        # Convenience properties
        self.house = self.agents.get("house")
        self.hal = self.agents.get("hal")
        # ... etc
```

### 6. Improved Models

Dataclasses now include docstrings and type hints:

```python
@dataclass
class Proposal:
    """Business opportunity proposal.
    
    Attributes:
        id: Unique proposal identifier
        title: Proposal title
        description: Full description
        channel: Distribution channel
        expected_revenue_pence: Expected revenue in pence
        expected_cost_pence: Expected cost in pence
        vulnerability_risk: Risk level ('low', 'medium', 'high')
        legal_confidence: Legality confidence (0.0-1.0)
        customer_value: Customer value perception (0.0-1.0)
        probability_of_sale: Probability of sale (0.0-1.0)
        hours_to_launch: Hours to launch product
        metadata: Additional metadata
    """
```

## Migration Guide

### If you were using the old monolithic structure:

**Old way:**
```python
from imaginarium.imaginarium import Imaginarium
app = Imaginarium()
app.hal.propose(...)
```

**New way:**
```python
from imaginarium import Imaginarium
app = Imaginarium()
app.hal.propose(...)
```

The API is the same, but the implementation is cleaner underneath.

### Adding a new agent

1. Create `imaginarium/agents/my_agent.py`:
```python
from imaginarium.agents import BaseAgent

class MyAgent(BaseAgent):
    def execute(self, *args, **kwargs):
        # Your logic here
        pass
```

2. Update `imaginarium/agents/__init__.py` — import and add to registry:
```python
from imaginarium.agents.my_agent import MyAgent

# In AgentRegistry._initialize_all():
agent_class = MyAgent  # ... etc
```

3. Add to `AgentRegistry.AGENT_SPECS`:
```python
AGENT_SPECS = {
    # ...
    "my_agent": {
        "lineage": "MyAgent",
        "role": "My Role",
        "class": "MyAgent",
    },
}
```

4. Test it:
```python
from imaginarium import Imaginarium
app = Imaginarium()
my_agent = app.agents.get("my_agent")
```

## Architecture Principles

### 1. **Single Responsibility**
Each agent has one clear role. Each module does one thing well.

### 2. **Immutable Core Laws**
Core Laws are read-only and cryptographically verified. No agent can modify them.

### 3. **Authority Hierarchy**
```
Core Laws (immutable)
    ↓
Primary Operator (you)
    ↓
Mr. House (permanent Overseer)
    ↓
Specialist Agents (Hydra-capable)
```

### 4. **Hard Vetoes**
GLaDOS (Compliance) and K-2SO (Treasury) have **hard veto** authority:
- Their decisions cannot be overridden
- They don't participate in Hydra (vetoes are success, not failure)
- Compliance and human safety override profit

### 5. **Hydra Protocol**
Specialist agents can be Hydra'd on operational failure:
- Failure retires the agent
- Two descendants are created with same role/lineage
- Both are benchmarked
- Higher-scoring descendant is promoted to active
- Mr. House cannot be Hydra'd (he is permanent and unique)

### 6. **Bounded Self-Improvement**
Agents can improve their prompts, workflows, and heuristics, but:
- Cannot modify protected components (Core Laws, Authority, Hydra exemption, etc.)
- Cannot gain authority or permissions
- Self-improvement is logged and requires measurable improvement

### 7. **Morale & Ceremony**
Verified productive behavior earns persistent Morale Points and ceremonial rewards:
- Can acknowledge achievement
- Cannot change permissions or override vetoes

## Running the Refactored System

### Demo mode
```bash
python -m imaginarium
```

This executes a single business cycle with a pre-formed idea.

### Run tests
```bash
python -m unittest discover imaginarium/tests -v
```

### Check status
```bash
python -c "from imaginarium import Imaginarium; app = Imaginarium(); print(app.status())"
```

### Python API
```python
from imaginarium import Imaginarium
import json

app = Imaginarium()

# Execute with custom idea
idea = {
    "title": "My Product",
    "description": "A genuine product for customers",
    "channel": "local storefront",
    "expected_revenue_pence": 1000,
    "expected_cost_pence": 0,
    "legal_confidence": 0.99,
    "customer_value": 0.8,
}

result = app.execute(idea)
print(json.dumps(result, indent=2))
```

## What's Next

Potential improvements enabled by modular architecture:

1. **AI Integration** — Plug Brain integration into individual agents
2. **Persistence** — Richer agent history and decision logs
3. **Monitoring** — Agent performance metrics and dashboards
4. **Extensibility** — Add new agents for specific business domains
5. **Modularity** — Use agents in different contexts (API endpoints, batch processing, etc.)
6. **Testing** — Easier to mock agents for integration tests

## Files Changed Summary

**New files (agents):**
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

**New files (tests):**
- `imaginarium/tests/__init__.py`
- `imaginarium/tests/test_all.py` — System integration tests
- `imaginarium/tests/test_agents.py` — Individual agent tests
- `imaginarium/tests/test_imports.py` — Package API tests

**Updated files:**
- `imaginarium/app.py` — Refactored for modular agents
- `imaginarium/services/pipeline.py` — Cleaner orchestration
- `imaginarium/core/models.py` — Enhanced with docstrings
- `imaginarium/__init__.py` — Public API exports
- `imaginarium/__main__.py` — Entry point

**Deprecated (old monolithic reference):**
- `imaginarium.py` — Can be removed (now split into modular structure)

---

**Status:** Ready for merge. All tests pass. Full backward compatibility maintained for public API.
