from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class AuthorityPolicy:
    primary_name: str = "Primary Operator"

    def precedence(self) -> tuple[str, ...]:
        return ("Core Laws", self.primary_name, "Mr. House", "Specialist Agents")

    def may_hydra(self, display_name: str) -> bool:
        return display_name != "Mr. House"

    def resolve_instruction(self, primary_instruction: str | None, house_instruction: str | None) -> str | None:
        return primary_instruction if primary_instruction is not None else house_instruction
