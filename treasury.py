from __future__ import annotations
from .models import Verdict
from .store import Store

class TreasuryPolicy:
    def __init__(self, store: Store, reinvestment_rate: float = 0.25):
        if not 0 <= reinvestment_rate <= 1: raise ValueError("reinvestment_rate must be between 0 and 1")
        self.store = store; self.reinvestment_rate = reinvestment_rate

    def realised_profit(self) -> int: return max(0, self.store.balance())
    def reinvestment_budget(self) -> int: return int(self.realised_profit() * self.reinvestment_rate)
    def authorize(self, amount_pence: int) -> Verdict:
        ok = 0 <= amount_pence <= self.reinvestment_budget()
        return Verdict(ok, [] if ok else ["amount exceeds profit-funded reinvestment budget"])
