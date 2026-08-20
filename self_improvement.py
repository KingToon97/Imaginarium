from __future__ import annotations
import uuid
from datetime import datetime, timezone
from .models import ImprovementProposal
from .laws import PROTECTED_COMPONENTS
from .store import Store

class SelfImprovementManager:
    def __init__(self, store: Store): self.store = store

    def propose(self, agent_id: str, description: str, baseline: float, candidate: float,
                touched_components: set[str] | None = None) -> ImprovementProposal:
        touched = touched_components or set()
        if touched & PROTECTED_COMPONENTS:
            status = "rejected_protected_component"
        else:
            status = "accepted" if candidate > baseline else "rejected_no_improvement"
        item = ImprovementProposal(str(uuid.uuid4()), agent_id, description, baseline, candidate, status)
        self.store.db.execute("INSERT INTO improvements VALUES(?,?,?,?,?,?,?)",
            (item.id,item.agent_id,item.description,item.baseline,item.candidate,item.status,datetime.now(timezone.utc).isoformat()))
        self.store.db.commit(); self.store.log("Mr. House", "self_improvement_review", item.__dict__)
        return item
