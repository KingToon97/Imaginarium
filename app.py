from __future__ import annotations
import json, os
from .core.store import Store
from .core.authority import AuthorityPolicy
from .core.hydra import HydraProtocol
from .core.morale import MoraleSystem
from .core.self_improvement import SelfImprovementManager
from .core.treasury import TreasuryPolicy
from .agents.house import MrHouse
from .agents.specialists import HAL,Cortana,GLaDOS,WALL_E,MrData,HK47,R2D2,Johnny5,TARS,K2SO,Skynet
from .services.pipeline import BusinessPipeline

class Imaginarium:
    def __init__(self, home=None):
        self.store=Store(home)
        self.authority=AuthorityPolicy(os.getenv("IMAGINARIUM_PRIMARY_NAME","Primary Operator"))
        self.house=MrHouse(self.store)
        self.hal=HAL("hal","HAL","Opportunity Agent",self.store)
        self.cortana=Cortana("cortana","Cortana","Market Analyst",self.store)
        self.glados=GLaDOS("glados","GLaDOS","Compliance Agent",self.store)
        self.walle=WALL_E("walle","WALL-E","Product/Service Builder",self.store)
        self.data=MrData("data","Mr. Data","Critic/QA Agent",self.store)
        self.hk=HK47("hk47","HK-47","Pricing Agent",self.store)
        self.r2=R2D2("r2d2","R2-D2","Publisher Agent",self.store)
        self.j5=Johnny5("johnny5","Johnny 5","Marketing Agent",self.store)
        self.tars=TARS("tars","TARS","Sales Analyst",self.store)
        self.k2=K2SO("k2so","K-2SO","Treasury Agent",self.store)
        self.skynet=Skynet("skynet","Skynet","Strategy Agent",self.store)
        self.morale=MoraleSystem(self.store)
        self.treasury=TreasuryPolicy(self.store,float(os.getenv("IMAGINARIUM_REINVESTMENT_RATE","0.25")))
        self.hydra=HydraProtocol(self.store,self.authority)
        self.self_improvement=SelfImprovementManager(self.store)
        self.pipeline=BusinessPipeline(self)

    def execute(self,idea:dict)->dict: return self.pipeline.execute(idea)

def demo():
    app=Imaginarium()
    idea={
        "title":"Freelance Project Budget Template",
        "description":"An original budgeting template for freelancers to estimate project costs and margins.",
        "channel":"local storefront / compliant marketplace adapter",
        "expected_revenue_pence":500,"expected_cost_pence":0,"vulnerability_risk":"low",
        "legal_confidence":.98,"customer_value":.8,"probability_of_sale":.2,"hours_to_launch":1.0,
    }
    print(json.dumps(app.execute(idea),indent=2)); print(f"Treasury balance: £{app.store.balance()/100:.2f}")
