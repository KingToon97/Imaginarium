from __future__ import annotations
import json
from datetime import datetime, timezone
from .authority import AuthorityPolicy
from .store import Store

class HydraProtocol:
    """Retires a failed specialist and creates two bounded successor records.

    Hydra never applies to Mr. House. Descendants inherit the same role/lineage and
    cannot alter permissions or protected controls. Benchmarking determines the winner.
    """
    def __init__(self, store: Store, authority: AuthorityPolicy): self.store=store; self.authority=authority

    def trigger(self, failed_agent_id: str, reason: str, benchmark_a: float, benchmark_b: float) -> dict:
        row=self.store.db.execute("SELECT * FROM agents WHERE agent_id=?",(failed_agent_id,)).fetchone()
        if row is None: raise KeyError(f"Unknown agent {failed_agent_id}")
        if not self.authority.may_hydra(row["display_name"]):
            raise PermissionError("Hydra cannot terminate, duplicate, fork, or replace Mr. House")
        self.store.set_status(failed_agent_id,"retired")
        generation=int(row["generation"])+1; base=row["lineage"].replace(" ","_").lower()
        child_a=f"{base}-h{generation}a"; child_b=f"{base}-h{generation}b"
        for cid,variant in ((child_a,"A"),(child_b,"B")):
            self.store.register_agent(agent_id=cid,lineage=row["lineage"],display_name=row["display_name"],role=row["role"],
                                      generation=generation,parent_id=failed_agent_id,variant=variant,status="candidate")
        winner=child_a if benchmark_a>=benchmark_b else child_b; loser=child_b if winner==child_a else child_a
        self.store.set_status(winner,"active"); self.store.set_status(loser,"archived")
        payload={"generation":generation,"benchmark_a":benchmark_a,"benchmark_b":benchmark_b,"loser":loser}
        self.store.db.execute("INSERT INTO hydra_events(ts,failed_agent_id,reason,child_a,child_b,winner,payload) VALUES(?,?,?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(),failed_agent_id,reason,child_a,child_b,winner,json.dumps(payload)))
        self.store.db.commit(); self.store.log("Mr. House","hydra",{"failed":failed_agent_id,"winner":winner,**payload})
        return {"failed":failed_agent_id,"children":[child_a,child_b],"winner":winner,"generation":generation}
