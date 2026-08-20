from __future__ import annotations
from imaginarium.core.laws import verify_core_integrity
from imaginarium.core.morale import MoraleSystem
from imaginarium.core.treasury import TreasuryPolicy

class BusinessPipeline:
    def __init__(self, company): self.company=company

    def execute(self, idea: dict) -> dict:
        c=self.company; verify_core_integrity()
        p=c.hal.propose(idea); score=c.cortana.score(p)
        cv=c.glados.review(p)
        if not cv.approved:
            c.morale.award(c.glados.agent_id,5,"correctly rejected non-compliant proposal")
            return {"status":"rejected_by_GLaDOS","reasons":cv.reasons}
        if p.expected_cost_pence:
            budget=c.treasury.reinvestment_budget(); tv=c.k2.authorize_spend(p.expected_cost_pence,budget)
            if not tv.approved:
                c.morale.award(c.k2.agent_id,5,"prevented unauthorised expenditure")
                return {"status":"rejected_by_K2SO","reasons":tv.reasons}
        artifact=c.walle.build(p); qa=c.data.qa(p,artifact)
        if not qa.approved:
            hydra=c.hydra.trigger(c.walle.agent_id,"artifact failed independent QA",benchmark_a=.51,benchmark_b=.52)
            return {"status":"rejected_by_Data","reasons":qa.reasons,"hydra":hydra}
        price=c.hk.price(p); publication=c.r2.publish(p,artifact); marketing=c.j5.market(p)
        c.morale.award(c.hal.agent_id,5,"compliant opportunity reached publication")
        c.morale.award(c.walle.agent_id,5,"artifact passed QA")
        c.morale.award(c.data.agent_id,5,"completed successful QA")
        result={"status":"live","proposal":p.id,"market_score":score,"price_pence":price,"publication":publication,"marketing":marketing}
        c.house.log("executed",result); return result
