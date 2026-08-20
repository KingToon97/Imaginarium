"""Modular specialist agents for Imaginarium autonomous business engine.

Each agent has a unique role, lineage, and authority ceiling defined by Core Laws.
Mr. House is the permanent unique Overseer. Specialist agents may be Hydra'd on failure.
"""
from __future__ import annotations
import uuid
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from imaginarium.core.store import Store

from imaginarium.core.models import Verdict


class BaseAgent(ABC):
    """Base class for all Imaginarium agents.
    
    Defines common lifecycle: initialization, decision-making, logging, morale.
    Subclasses implement role-specific logic (e.g., compliance review, artifact building).
    """

    def __init__(
        self,
        agent_id: str,
        lineage: str,
        display_name: str,
        role: str,
        store: Store,
        generation: int = 0,
        parent_id: str | None = None,
    ):
        """Initialize an agent.
        
        Args:
            agent_id: Unique identifier (e.g., 'hal', 'glados-h1a')
            lineage: Base name for Hydra lineage (e.g., 'HAL', 'GLaDOS')
            display_name: Human-readable name
            role: Role description (e.g., 'Opportunity Agent')
            store: Shared SQLite Store instance
            generation: Hydra generation (0 for original, 1+ for descendants)
            parent_id: Parent agent_id if created by Hydra
        """
        self.agent_id = agent_id
        self.lineage = lineage
        self.display_name = display_name
        self.role = role
        self.store = store
        self.generation = generation
        self.parent_id = parent_id
        self._register()

    def _register(self) -> None:
        """Register this agent in the store and initialize morale."""
        self.store.register_agent(
            agent_id=self.agent_id,
            lineage=self.lineage,
            display_name=self.display_name,
            role=self.role,
            generation=self.generation,
            status="active",
            parent_id=self.parent_id,
        )

    def log(self, action: str, payload: Any) -> None:
        """Log an action to the audit trail."""
        self.store.log(self.display_name, action, payload)

    def reward(self, points: int, reason: str, ceremony: str = "") -> None:
        """Earn morale points for verified productive behavior."""
        self.store.reward(self.agent_id, points, reason, ceremony)

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """Role-specific execution. Implemented by subclasses."""
        pass


class AgentRegistry:
    """Factory and registry for all agents in the system.
    
    Manages creation, lookup, and lifecycle of agents across the business.
    Ensures Mr. House is unique and permanent.
    """

    AGENT_SPECS = {
        "house": {
            "lineage": "Mr. House",
            "role": "Overseer",
            "class": "MrHouse",
        },
        "hal": {
            "lineage": "HAL",
            "role": "Opportunity Agent",
            "class": "HAL",
        },
        "cortana": {
            "lineage": "Cortana",
            "role": "Market Analyst",
            "class": "Cortana",
        },
        "glados": {
            "lineage": "GLaDOS",
            "role": "Compliance Agent",
            "class": "GLaDOS",
        },
        "walle": {
            "lineage": "WALL-E",
            "role": "Product/Service Builder",
            "class": "WALL_E",
        },
        "data": {
            "lineage": "Mr. Data",
            "role": "Critic/QA Agent",
            "class": "MrData",
        },
        "hk47": {
            "lineage": "HK-47",
            "role": "Pricing Agent",
            "class": "HK47",
        },
        "r2d2": {
            "lineage": "R2-D2",
            "role": "Publisher Agent",
            "class": "R2D2",
        },
        "johnny5": {
            "lineage": "Johnny 5",
            "role": "Marketing Agent",
            "class": "Johnny5",
        },
        "tars": {
            "lineage": "TARS",
            "role": "Sales Analyst",
            "class": "TARS",
        },
        "k2so": {
            "lineage": "K-2SO",
            "role": "Treasury Agent",
            "class": "K2SO",
        },
        "skynet": {
            "lineage": "Skynet",
            "role": "Strategy Agent",
            "class": "Skynet",
        },
    }

    def __init__(self, store: Store):
        self.store = store
        self._agents: dict[str, BaseAgent] = {}
        self._initialize_all()

    def _initialize_all(self) -> None:
        """Initialize all default agents at startup."""
        # Import here to avoid circular imports
        from imaginarium.agents.overseer import MrHouse
        from imaginarium.agents.opportunity import HAL
        from imaginarium.agents.market import Cortana
        from imaginarium.agents.compliance import GLaDOS
        from imaginarium.agents.builder import WALL_E
        from imaginarium.agents.qa import MrData
        from imaginarium.agents.pricing import HK47
        from imaginarium.agents.publisher import R2D2
        from imaginarium.agents.marketing import Johnny5
        from imaginarium.agents.sales import TARS
        from imaginarium.agents.treasury_agent import K2SO
        from imaginarium.agents.strategy import Skynet

        agent_classes = {
            "MrHouse": MrHouse,
            "HAL": HAL,
            "Cortana": Cortana,
            "GLaDOS": GLaDOS,
            "WALL_E": WALL_E,
            "MrData": MrData,
            "HK47": HK47,
            "R2D2": R2D2,
            "Johnny5": Johnny5,
            "TARS": TARS,
            "K2SO": K2SO,
            "Skynet": Skynet,
        }

        for agent_id, spec in self.AGENT_SPECS.items():
            agent_class = agent_classes[spec["class"]]
            agent = agent_class(
                agent_id=agent_id,
                lineage=spec["lineage"],
                display_name=spec["lineage"],
                role=spec["role"],
                store=self.store,
            )
            self._agents[agent_id] = agent

    def get(self, agent_id: str) -> BaseAgent:
        """Retrieve an agent by ID."""
        if agent_id not in self._agents:
            raise KeyError(f"Unknown agent: {agent_id}")
        return self._agents[agent_id]

    def all(self) -> dict[str, BaseAgent]:
        """Return all registered agents."""
        return self._agents.copy()

    def register_hydra_descendants(
        self,
        parent_id: str,
        child_a_id: str,
        child_b_id: str,
        benchmark_a: float,
        benchmark_b: float,
    ) -> tuple[BaseAgent, BaseAgent]:
        """Create two descendant agents from a Hydra event.
        
        Args:
            parent_id: Parent agent ID
            child_a_id: First child ID
            child_b_id: Second child ID
            benchmark_a: Performance score for child A
            benchmark_b: Performance score for child B
            
        Returns:
            Tuple of (child_a, child_b) agent instances
        """
        from imaginarium.agents.overseer import MrHouse
        from imaginarium.agents.opportunity import HAL
        from imaginarium.agents.market import Cortana
        from imaginarium.agents.compliance import GLaDOS
        from imaginarium.agents.builder import WALL_E
        from imaginarium.agents.qa import MrData
        from imaginarium.agents.pricing import HK47
        from imaginarium.agents.publisher import R2D2
        from imaginarium.agents.marketing import Johnny5
        from imaginarium.agents.sales import TARS
        from imaginarium.agents.treasury_agent import K2SO
        from imaginarium.agents.strategy import Skynet

        agent_classes = {
            "MrHouse": MrHouse,
            "HAL": HAL,
            "Cortana": Cortana,
            "GLaDOS": GLaDOS,
            "WALL_E": WALL_E,
            "MrData": MrData,
            "HK47": HK47,
            "R2D2": R2D2,
            "Johnny5": Johnny5,
            "TARS": TARS,
            "K2SO": K2SO,
            "Skynet": Skynet,
        }

        parent = self.get(parent_id)
        agent_class = type(parent)

        child_a = agent_class(
            agent_id=child_a_id,
            lineage=parent.lineage,
            display_name=parent.display_name,
            role=parent.role,
            store=self.store,
            generation=parent.generation + 1,
            parent_id=parent_id,
        )
        child_b = agent_class(
            agent_id=child_b_id,
            lineage=parent.lineage,
            display_name=parent.display_name,
            role=parent.role,
            store=self.store,
            generation=parent.generation + 1,
            parent_id=parent_id,
        )

        self._agents[child_a_id] = child_a
        self._agents[child_b_id] = child_b
        return child_a, child_b


__all__ = [
    "BaseAgent",
    "AgentRegistry",
]
