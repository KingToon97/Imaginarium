from __future__ import annotations
import random
from .store import Store

REWARD_TITLES = (
    "Golden Cog",
    "Distinguished Service Citation",
    "Imaginarium Laureate",
    "Precision Star",
    "First-Class Merit Badge",
)

class MoraleSystem:
    def __init__(self, store: Store): self.store = store
    def award(self, agent_id: str, points: int, reason: str) -> str:
        ceremonial = random.choice(REWARD_TITLES)
        self.store.reward(agent_id, points, reason, ceremonial)
        return ceremonial
