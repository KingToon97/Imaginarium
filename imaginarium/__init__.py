"""Imaginarium: Bounded autonomous multi-agent business scaffold.

Starts with £0 initial capital. Discovers, builds, prices, and publishes
original digital products entirely through specialized AI agents constrained
by immutable Core Laws.

Core principle: Compliance and human safety override profit.
"""
__version__ = "4.0.0"
__author__ = "KingToon97"

from imaginarium.app import Imaginarium
from imaginarium.agents import BaseAgent, AgentRegistry
from imaginarium.core.models import Proposal, Verdict

__all__ = [
    "Imaginarium",
    "BaseAgent",
    "AgentRegistry",
    "Proposal",
    "Verdict",
]
