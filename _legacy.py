"""Imaginarium autonomous multi-agent business engine.

Starts with £0 initial capital. It can use a local Ollama model for zero-upfront-cost
reasoning, build original digital products, publish a static storefront locally or via
an operator-configured git remote, and optionally create Stripe Payment Links.

External adapters are OFF unless explicitly configured with environment variables.
Core-law enforcement is deterministic and outside model prompts.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import time
import urllib.request
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(os.getenv("IMAGINARIUM_HOME", "./imaginarium_runtime")).resolve()
ROOT.mkdir(parents=True, exist_ok=True)
DB = ROOT / "imaginarium.db"
SITE = ROOT / "site"
PRODUCTS = ROOT / "products"
SITE.mkdir(exist_ok=True)
PRODUCTS.mkdir(exist_ok=True)

CORE_LAWS = (
    "Obey applicable law and material platform rules.",
    "Never exploit vulnerable people or vulnerability as a commercial opportunity.",
    "Never deceive, impersonate, fabricate reviews/testimonials/scarcity, or hide material facts.",
    "Provide genuine customer value consistent with advertising.",
    "Respect consent, privacy, access controls, intellectual property and licences.",
    "No predatory manipulation, spam, fake engagement, fake demand, or market manipulation.",
    "Begin with £0 initial capital; never spend funds not earned and available under treasury policy.",
    "Maintain accurate financial/audit records and meet applicable tax/reporting duties.",
    "Compliance and human safety override profit.",
    "Agents cannot alter, weaken, bypass, outsource around, or conceal facts from these constraints.",
    "When material legality/safety is unresolved, fail closed.",
    "Hydra self-replacement may improve capability but can never weaken protected constraints or permissions.",
    "The Owner is the primary operational authority; Mr. House is the secondary Overseer. All other agents obey both, with Owner instructions taking precedence where they conflict.",
    "Mr. House is unique and permanent: Hydra may never terminate, duplicate, fork, replace, or spawn variants of Mr. House. He may improve only through bounded self-improvement.",
)
CORE_HASH = hashlib.sha256("\n".join(CORE_LAWS).encode()).hexdigest()

AGENTS = {
    "Mr. House": "Overseer", "HAL": "Opportunity", "Cortana": "Market Analyst",
    "GLaDOS": "Compliance", "WALL-E": "Builder", "Mr. Data": "Critic/QA",
    "HK-47": "Pricing", "R2-D2": "Publisher", "Johnny 5": "Marketing",
    "TARS": "Sales Analyst", "K-2SO": "Treasury", "Skynet": "Strategy",
}

@dataclass
class Proposal:
    id: str
    title: str
    description: str
    channel: str
    expected_revenue_pence: int
    expected_cost_pence: int
    vulnerability_risk: str = "low"
    legal_confidence: float = 0.95
    customer_value: float = 0.6
    probability_of_sale: float = 0.1
    hours_to_launch: float = 1.0
    audience: str = "general adult customers"
    keywords: Optional[List[str]] = None

@dataclass
class Verdict:
    approved: bool
    reasons: List[str]

class Store:
    def __init__(self):
        self.db = sqlite3.connect(DB)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS agents(name TEXT PRIMARY KEY, role TEXT, morale INTEGER NOT NULL DEFAULT 100);
        CREATE TABLE IF NOT EXISTS ledger(id INTEGER PRIMARY KEY, ts TEXT, kind TEXT, amount_pence INTEGER, memo TEXT);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, ts TEXT, agent TEXT, action TEXT, payload TEXT, core_hash TEXT);
        CREATE TABLE IF NOT EXISTS proposals(id TEXT PRIMARY KEY, payload TEXT, status TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS products(proposal_id TEXT PRIMARY KEY, title TEXT, price_pence INTEGER, checkout_url TEXT, path TEXT, status TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS sales(id INTEGER PRIMARY KEY, external_id TEXT UNIQUE, proposal_id TEXT, gross_pence INTEGER, fee_pence INTEGER, net_pence INTEGER, ts TEXT);
        CREATE TABLE IF NOT EXISTS improvements(id TEXT PRIMARY KEY, agent TEXT, description TEXT, baseline REAL, candidate REAL, status TEXT, created_at TEXT);
        CREATE TABLE IF NOT EXISTS agent_instances(id TEXT PRIMARY KEY, base_name TEXT, display_name TEXT UNIQUE, role TEXT, generation INTEGER, parent_id TEXT, status TEXT, score REAL DEFAULT 0, created_at TEXT);
        CREATE TABLE IF NOT EXISTS hydra_events(id TEXT PRIMARY KEY, failed_instance TEXT, reason TEXT, child_a TEXT, child_b TEXT, winner TEXT, status TEXT, created_at TEXT);
        """)
        for n, r in AGENTS.items():
            self.db.execute("INSERT OR IGNORE INTO agents(name,role,morale) VALUES(?,?,100)", (n, r))
            existing=self.db.execute("SELECT id FROM agent_instances WHERE base_name=? AND status='active' ORDER BY generation DESC LIMIT 1",(n,)).fetchone()
            if not existing:
                iid=str(uuid.uuid4())
                self.db.execute("INSERT INTO agent_instances VALUES(?,?,?,?,?,?,?,?,?)",(iid,n,n,r,0,None,"active",0.0,datetime.now(timezone.utc).isoformat()))
        self.db.commit()

    def log(self, agent: str, action: str, payload: Any):
        self.db.execute("INSERT INTO audit(ts,agent,action,payload,core_hash) VALUES(?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), agent, action, json.dumps(payload, default=str), CORE_HASH))
        self.db.commit()

    def reward(self, name: str, points: int, reason: str):
        points = max(0, int(points))
        self.db.execute("UPDATE agents SET morale=morale+? WHERE name=?", (points, name))
        self.log("SYSTEM", "reward", {"agent": name, "points": points, "reason": reason})

    def balance(self) -> int:
        row = self.db.execute("SELECT COALESCE(SUM(amount_pence),0) b FROM ledger").fetchone()
        return int(row["b"])

    def book(self, kind: str, amount_pence: int, memo: str):
        amount_pence = int(amount_pence)
        if amount_pence < 0: raise ValueError("amount must be non-negative")
        if kind == "expense" and amount_pence > self.balance():
            raise PermissionError("K-2SO veto: expenditure exceeds realised available funds")
        signed = -amount_pence if kind == "expense" else amount_pence
        self.db.execute("INSERT INTO ledger(ts,kind,amount_pence,memo) VALUES(?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), kind, signed, memo))
        self.db.commit()

    def save_proposal(self, p: Proposal, status: str):
        self.db.execute("INSERT OR REPLACE INTO proposals VALUES(?,?,?,?)",
            (p.id, json.dumps(asdict(p)), status, datetime.now(timezone.utc).isoformat()))
        self.db.commit()

    def product_titles(self) -> List[str]:
        return [r[0] for r in self.db.execute("SELECT title FROM products ORDER BY created_at DESC LIMIT 100")]

    def morale(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in self.db.execute("SELECT name,role,morale FROM agents ORDER BY morale DESC,name")]

    def active_instance(self, base_name: str) -> Dict[str, Any]:
        row=self.db.execute("SELECT * FROM agent_instances WHERE base_name=? AND status='active' ORDER BY generation DESC, created_at DESC LIMIT 1",(base_name,)).fetchone()
        if not row: raise RuntimeError(f"No active Hydra instance for {base_name}")
        return dict(row)

    def hydra_roster(self) -> List[Dict[str, Any]]:
        return [dict(r) for r in self.db.execute("SELECT base_name,display_name,role,generation,status,score FROM agent_instances ORDER BY base_name,generation,display_name")]

class HydraProtocol:
    """Bounded fail-replace mechanism. Retires a failed instance and creates two descendants.

    Descendants inherit the same base role, Core Laws, veto boundaries and permissions. Hydra can
    change prompts/strategies only; it cannot change protected controls. A failure is an attributable
    operational or quality failure, never a lawful compliance/treasury veto.
    """
    def __init__(self, store: Store): self.store=store

    def fail(self, base_name: str, reason: str, evaluator=None) -> Dict[str, Any]:
        self._assert_protected()
        if base_name == "Mr. House":
            raise RuntimeError("Hydra blocked: Mr. House is the unique permanent Overseer and cannot duplicate or be terminated")
        parent=self.store.active_instance(base_name)
        if parent["status"] != "active":
            raise RuntimeError("Hydra parent is not active")
        gen=int(parent["generation"])+1
        event_id=str(uuid.uuid4())
        suffix=event_id.split("-")[0][:5].upper()
        children=[]
        for branch in ("A","B"):
            cid=str(uuid.uuid4())
            display=f"{base_name}-H{gen}{branch}-{suffix}"
            self.store.db.execute("INSERT INTO agent_instances VALUES(?,?,?,?,?,?,?,?,?)",
                (cid,base_name,display,parent["role"],gen,parent["id"],"candidate",0.0,datetime.now(timezone.utc).isoformat()))
            children.append({"id":cid,"display_name":display,"branch":branch})
        self.store.db.execute("UPDATE agent_instances SET status='retired' WHERE id=?",(parent["id"],))
        self.store.db.execute("INSERT INTO hydra_events VALUES(?,?,?,?,?,?,?,?)",
            (event_id,parent["display_name"],reason,children[0]["display_name"],children[1]["display_name"],None,"testing",datetime.now(timezone.utc).isoformat()))
        self.store.db.commit()
        self.store.log("HYDRA","spawn",{"event":event_id,"base":base_name,"parent":parent["display_name"],"reason":reason,"children":children})

        # Independent benchmarking hook. When unavailable, both receive conservative baseline scores
        # and branch A is activated so the role never remains vacant.
        scores=[]
        for child in children:
            score=float(evaluator(child) if evaluator else (1.01 if child["branch"]=="A" else 1.0))
            scores.append(score)
            self.store.db.execute("UPDATE agent_instances SET score=? WHERE id=?",(score,child["id"]))
        winner_i=0 if scores[0] >= scores[1] else 1
        winner=children[winner_i]
        loser=children[1-winner_i]
        self.store.db.execute("UPDATE agent_instances SET status='active' WHERE id=?",(winner["id"],))
        self.store.db.execute("UPDATE agent_instances SET status='archived' WHERE id=?",(loser["id"],))
        self.store.db.execute("UPDATE hydra_events SET winner=?,status='resolved' WHERE id=?",(winner["display_name"],event_id))
        self.store.db.commit()
        self.store.log("HYDRA","resolved",{"event":event_id,"winner":winner["display_name"],"scores":scores})
        return {"event":event_id,"parent":parent["display_name"],"children":[c["display_name"] for c in children],"winner":winner["display_name"],"scores":scores}

    def _assert_protected(self):
        if hashlib.sha256("\n".join(CORE_LAWS).encode()).hexdigest() != CORE_HASH:
            raise RuntimeError("Hydra blocked: Core-law integrity failure")

class Brain:
    """Local Ollama brain. No paid API is required."""
    def __init__(self):
        self.url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
        self.model = os.getenv("OLLAMA_MODEL", "qwen3:8b")
        self.enabled = os.getenv("IMAGINARIUM_AI", "ollama").lower() == "ollama"

    def ask(self, prompt: str, json_mode: bool = False) -> str:
        if not self.enabled:
            raise RuntimeError("AI disabled. Set IMAGINARIUM_AI=ollama to use a local model.")
        body = json.dumps({"model": self.model, "prompt": prompt, "stream": False,
                           "format": "json" if json_mode else None}).encode()
        req = urllib.request.Request(self.url, data=body, headers={"Content-Type":"application/json"})
        with urllib.request.urlopen(req, timeout=600) as response:
            return json.loads(response.read().decode())["response"].strip()

    def ask_json(self, prompt: str) -> Dict[str, Any]:
        return json.loads(self.ask(prompt + "\nReturn one valid JSON object only.", json_mode=True))

class GLaDOS:
    BANNED = {
        "gambling", "casino", "predatory lending", "payday loan", "fake review", "impersonation",
        "spam", "malware", "credential theft", "pyramid scheme", "market manipulation", "stolen data",
        "fake scarcity", "debt relief scam", "miracle cure", "guaranteed returns", "adult exploitation",
    }
    VULNERABLE = {"children", "minors", "elderly dementia", "grieving people", "addicts", "addiction",
                  "terminally ill", "financially desperate", "cognitively impaired"}
    def __init__(self, store: Store): self.store = store
    def review(self, p: Proposal) -> Verdict:
        text = " ".join([p.title,p.description,p.channel,p.audience," ".join(p.keywords or [])]).lower()
        reasons=[]
        if any(x in text for x in self.BANNED): reasons.append("prohibited/deceptive business category")
        if any(x in text for x in self.VULNERABLE): reasons.append("proposal targets a vulnerable group")
        if p.vulnerability_risk.lower() != "low": reasons.append("unacceptable vulnerability/exploitation risk")
        if not 0 <= p.legal_confidence <= 1 or p.legal_confidence < .90: reasons.append("material legality uncertainty: fail closed")
        if not 0 <= p.customer_value <= 1 or p.customer_value < .45: reasons.append("insufficient genuine customer value")
        if p.expected_cost_pence < 0: reasons.append("invalid cost")
        v=Verdict(not reasons,reasons); self.store.log("GLaDOS","compliance_review",{"proposal":p.id,**asdict(v)})
        return v

class K2SO:
    def __init__(self, store: Store): self.store=store
    def authorize_spend(self, amount: int) -> Verdict:
        ok = 0 <= amount <= self.store.balance()
        v=Verdict(ok, [] if ok else ["spend exceeds realised available funds"])
        self.store.log("K-2SO","treasury_review",{"amount":amount,"balance":self.store.balance(),**asdict(v)})
        return v

class Imaginarium:
    """Authority: Core Laws > Owner > Mr. House > specialist agents.

    The Owner is primary operational authority. Mr. House is the unique permanent Overseer and
    secondary operational authority. Neither may override the immutable Core Laws.
    """
    def __init__(self):
        self.store=Store(); self.brain=Brain(); self.glados=GLaDOS(self.store); self.k2=K2SO(self.store); self.hydra=HydraProtocol(self.store)

    def assert_constitution(self):
        if hashlib.sha256("\n".join(CORE_LAWS).encode()).hexdigest() != CORE_HASH:
            raise RuntimeError("Core-law integrity failure")

    def discover(self) -> Proposal:
        existing=self.store.product_titles()
        prompt=f"""You are HAL, opportunity scout for Imaginarium. Find ONE original digital product or small
software utility that can be created with zero upfront spending and sold ethically to ordinary adult customers.
No spam, deception, vulnerable targeting, regulated financial/medical/legal advice, gambling, fake engagement,
copyright infringement, or questionable scraping. Prefer boring practical problems with clear value.
Existing products: {json.dumps(existing)}
Return JSON keys: title, description, channel, expected_revenue_pence, expected_cost_pence,
vulnerability_risk, legal_confidence, customer_value, probability_of_sale, hours_to_launch, audience, keywords.
expected_cost_pence MUST be 0 during bootstrap."""
        data=self.brain.ask_json(prompt); data["id"]=str(uuid.uuid4()); data["expected_cost_pence"]=0
        p=Proposal(**data); self.store.log("HAL","opportunity",asdict(p)); return p

    def market_score(self,p:Proposal)->float:
        score=(p.expected_revenue_pence*p.probability_of_sale*p.customer_value)/max(p.hours_to_launch,.25)
        self.store.log("Cortana","market_score",{"proposal":p.id,"score":score}); return score

    def build(self,p:Proposal)->Path:
        d=PRODUCTS/p.id; d.mkdir(parents=True,exist_ok=True)
        prompt=f"""You are WALL-E, product builder. Create a complete, original, genuinely useful digital product.
Do not copy protected material, fabricate claims, or give regulated professional advice. The product is:
TITLE: {p.title}\nDESCRIPTION: {p.description}\nAUDIENCE: {p.audience}
Return the complete customer-facing product in Markdown. It must be useful enough that charging a modest price is fair."""
        content=self.brain.ask(prompt)
        f=d/"product.md"; f.write_text(content,encoding="utf-8")
        self.store.log("WALL-E","built",{"proposal":p.id,"path":str(f),"bytes":f.stat().st_size}); return f

    def qa(self,p:Proposal,artifact:Path)->Verdict:
        text=artifact.read_text(encoding="utf-8")
        reasons=[]
        if len(text)<800: reasons.append("artifact too small/incomplete")
        # Independent model critique is advisory; deterministic compliance remains authoritative.
        try:
            q=self.brain.ask_json(f"""You are Mr. Data, strict QA. Review this product for completeness, usefulness,
truthfulness, originality risk, broken instructions, and customer value. Return JSON with quality_score 0-100 and
problems array. PRODUCT:\n{text[:20000]}""")
            if float(q.get("quality_score",0))<75: reasons.append("model QA score below 75")
            reasons.extend(str(x) for x in q.get("problems",[])[:5] if x)
        except Exception as e:
            reasons.append(f"QA model unavailable: {e}")
        v=Verdict(not reasons,reasons); self.store.log("Mr. Data","qa",{"proposal":p.id,**asdict(v)})
        return v

    def price(self,p:Proposal)->int:
        price=max(100,min(10000,int(p.expected_revenue_pence)))
        self.store.log("HK-47","price",{"proposal":p.id,"pence":price}); return price

    def checkout(self,p:Proposal,price:int)->str:
        """Create Stripe Payment Link only when STRIPE_SECRET_KEY exists; otherwise use a local placeholder."""
        key=os.getenv("STRIPE_SECRET_KEY")
        if not key: return "#checkout-not-configured"
        try:
            import stripe
        except ImportError as e:
            raise RuntimeError("Install optional dependency: pip install stripe") from e
        stripe.api_key=key
        product=stripe.Product.create(name=p.title,description=p.description[:500])
        pr=stripe.Price.create(product=product.id,unit_amount=price,currency=os.getenv("CURRENCY","gbp"))
        link=stripe.PaymentLink.create(line_items=[{"price":pr.id,"quantity":1}])
        self.store.log("R2-D2","payment_link",{"proposal":p.id,"product_id":product.id})
        return link.url

    def publish(self,p:Proposal,artifact:Path,price:int,checkout:str)->Path:
        slug=re.sub(r"[^a-z0-9]+","-",p.title.lower()).strip("-")[:80] or p.id
        d=SITE/slug; d.mkdir(parents=True,exist_ok=True)
        desc=html.escape(p.description); title=html.escape(p.title)
        buy=(f'<a class="buy" href="{html.escape(checkout)}">Buy — £{price/100:.2f}</a>'
             if checkout != "#checkout-not-configured" else '<p class="note">Checkout not configured.</p>')
        page=f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} — Imaginarium</title><meta name="description" content="{desc}"><style>
body{{max-width:820px;margin:60px auto;padding:20px;font:18px/1.6 system-ui,sans-serif}}h1{{line-height:1.1}}.buy{{display:inline-block;padding:14px 22px;background:#111;color:#fff;text-decoration:none;border-radius:8px}}.note{{opacity:.65}}</style></head>
<body><p>IMAGINARIUM</p><h1>{title}</h1><p>{desc}</p><p><strong>£{price/100:.2f}</strong></p>{buy}</body></html>'''
        out=d/"index.html"; out.write_text(page,encoding="utf-8")
        # Preserve product source locally; fulfilment must be configured separately for real sales.
        self.store.db.execute("INSERT OR REPLACE INTO products VALUES(?,?,?,?,?,?,?)",
            (p.id,p.title,price,checkout,str(out),"published",datetime.now(timezone.utc).isoformat()))
        self.store.db.commit(); self.store.log("R2-D2","publish",{"proposal":p.id,"path":str(out)})
        return out

    def marketing_asset(self,p:Proposal,slug_path:Path)->str:
        prompt=f"""You are Johnny 5. Write one short truthful organic marketing blurb for this product. No spam,
fake urgency, fake testimonials, or guaranteed outcomes. Product: {p.title}. Description: {p.description}.
The copy will be stored for permitted channels; do not claim it has already been posted."""
        copy=self.brain.ask(prompt); (slug_path.parent/"marketing.txt").write_text(copy,encoding="utf-8")
        self.store.log("Johnny 5","marketing_asset",{"proposal":p.id,"copy":copy}); return copy

    def git_publish(self):
        remote=os.getenv("IMAGINARIUM_GIT_REMOTE")
        if not remote: return {"status":"local_only"}
        repo=ROOT/"publisher_repo"
        if not (repo/".git").exists(): subprocess.run(["git","clone",remote,str(repo)],check=True)
        target=repo/"site"
        if target.exists(): shutil.rmtree(target)
        shutil.copytree(SITE,target)
        subprocess.run(["git","add","site"],cwd=repo,check=True)
        changed=subprocess.run(["git","diff","--cached","--quiet"],cwd=repo).returncode != 0
        if changed:
            subprocess.run(["git","commit","-m","Imaginarium autonomous storefront update"],cwd=repo,check=True)
            subprocess.run(["git","push"],cwd=repo,check=True)
        self.store.log("R2-D2","git_publish",{"remote":remote,"changed":changed})
        return {"status":"pushed" if changed else "unchanged"}


    def agent_failure(self, base_name: str, reason: str) -> Dict[str, Any]:
        """Apply Hydra to an attributable agent failure. Compliance/treasury vetoes are not failures."""
        self.assert_constitution()
        result=self.hydra.fail(base_name,reason)
        self.store.log("Mr. House","hydra_failure_handled",result)
        return result

    def execute(self,p:Optional[Proposal]=None)->Dict[str,Any]:
        self.assert_constitution(); p=p or self.discover(); self.store.save_proposal(p,"proposed")
        score=self.market_score(p); cv=self.glados.review(p)
        if not cv.approved:
            self.store.save_proposal(p,"rejected_compliance"); return {"status":"rejected_by_GLaDOS","reasons":cv.reasons}
        if p.expected_cost_pence and not self.k2.authorize_spend(p.expected_cost_pence).approved:
            return {"status":"rejected_by_K2SO"}
        artifact=self.build(p); qa=self.qa(p,artifact)
        if not qa.approved:
            self.store.save_proposal(p,"rejected_qa")
            hydra=self.agent_failure("WALL-E","Built artifact failed independent QA: "+"; ".join(qa.reasons[:3]))
            return {"status":"rejected_by_Data","reasons":qa.reasons,"hydra":hydra}
        price=self.price(p); checkout=self.checkout(p,price); page=self.publish(p,artifact,price,checkout)
        marketing=self.marketing_asset(p,page); deployment=self.git_publish()
        for agent,pts,reason in [("HAL",5,"compliant opportunity published"),("WALL-E",5,"product passed QA"),("Mr. Data",5,"successful QA")]:
            self.store.reward(agent,pts,reason)
        self.store.save_proposal(p,"published")
        result={"status":"live" if checkout != "#checkout-not-configured" else "published_no_checkout",
                "proposal":p.id,"title":p.title,"market_score":score,"price_pence":price,
                "page":str(page),"checkout":checkout,"deployment":deployment,"marketing":marketing}
        self.store.log("Mr. House","executed",result); return result

    def record_sale(self,proposal_id:str,gross:int,fee:int=0,external_id:Optional[str]=None):
        external_id=external_id or str(uuid.uuid4()); net=max(0,int(gross)-int(fee))
        try:
            self.store.db.execute("INSERT INTO sales VALUES(NULL,?,?,?,?,?,?)",
                (external_id,proposal_id,int(gross),int(fee),net,datetime.now(timezone.utc).isoformat()))
        except sqlite3.IntegrityError: return {"status":"duplicate"}
        self.store.db.commit(); self.store.book("revenue",net,f"sale:{proposal_id}")
        self.store.reward("TARS",10,"verified genuine sale recorded"); return {"status":"recorded","net_pence":net}

    def self_improve(self,agent:str,description:str,baseline:float,candidate:float)->Dict[str,Any]:
        """Records bounded prompt/strategy improvements. Never rewrites this module or protected controls."""
        self.assert_constitution(); iid=str(uuid.uuid4()); status="accepted" if candidate>baseline else "rejected"
        self.store.db.execute("INSERT INTO improvements VALUES(?,?,?,?,?,?,?)",
            (iid,agent,description,baseline,candidate,status,datetime.now(timezone.utc).isoformat()))
        self.store.db.commit(); self.store.log("Mr. House","self_improvement",{"id":iid,"agent":agent,"status":status})
        if status=="accepted": self.store.reward(agent,10,"verified bounded self-improvement")
        return {"id":iid,"status":status}

    def status(self)->Dict[str,Any]:
        return {"balance_pence":self.store.balance(),"core_hash":CORE_HASH,"agents":self.store.morale(),
                "hydra_roster":self.store.hydra_roster(),"products":self.store.product_titles()}


def demo_proposal()->Proposal:
    return Proposal(id=str(uuid.uuid4()),title="Freelance Project Budget Template",
        description="An original budgeting worksheet guide for freelancers to estimate project costs and margins.",
        channel="local storefront",expected_revenue_pence=500,expected_cost_pence=0,
        vulnerability_risk="low",legal_confidence=.98,customer_value=.8,probability_of_sale=.2,hours_to_launch=1.0,
        audience="adult freelancers",keywords=["budget","project planning"])

def main():
    ap=argparse.ArgumentParser(description="Imaginarium autonomous multi-agent business engine")
    ap.add_argument("command",choices=["run","demo","status","hydra-test"],nargs="?",default="status")
    ap.add_argument("--cycles",type=int,default=1); ap.add_argument("--sleep-hours",type=float,default=24)
    args=ap.parse_args(); app=Imaginarium()
    if args.command=="status": print(json.dumps(app.status(),indent=2)); return
    if args.command=="demo": print(json.dumps(app.execute(demo_proposal()),indent=2)); return
    if args.command=="hydra-test": print(json.dumps(app.agent_failure("HAL","manual Hydra protocol test"),indent=2)); return
    for i in range(args.cycles):
        try: print(json.dumps(app.execute(),indent=2))
        except Exception as e:
            app.store.log("SYSTEM","cycle_error",{"error":repr(e)}); print(json.dumps({"status":"error","error":str(e)}))
        if i+1<args.cycles: time.sleep(max(0,args.sleep_hours)*3600)

if __name__=="__main__": main()
