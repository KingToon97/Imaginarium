from __future__ import annotations
from ..store import Store


class MrHouse:
    """Unique permanent Overseer. Hydra may never apply to Mr. House."""

    agent_id = "house"
    display_name = "Mr. House"

    def __init__(self, store: Store):
        self.store = store
        store.register_agent(
            agent_id=self.agent_id,
            lineage="Mr. House",
            display_name=self.display_name,
            role="Overseer",
        )

    def log(self, action: str, payload: object) -> None:
        self.store.log(self.display_name, action, payload)
