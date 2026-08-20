from __future__ import annotations
import json, os, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .laws import CORE_HASH

class Store:
    def __init__(self, home: str | Path | None = None):
        root = Path(home or os.getenv("IMAGINARIUM_HOME", "./runtime"))
        root.mkdir(parents=True, exist_ok=True)
        self.root = root
        self.db_path = root / "imaginarium.db"
        self.db = sqlite3.connect(self.db_path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS agents(
            agent_id TEXT PRIMARY KEY, lineage TEXT, display_name TEXT, role TEXT,
            generation INTEGER, status TEXT, morale INTEGER DEFAULT 100,
            parent_id TEXT, variant TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS ledger(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT,
            amount_pence INTEGER, memo TEXT
        );
        CREATE TABLE IF NOT EXISTS audit(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, agent TEXT,
            action TEXT, payload TEXT, core_hash TEXT
        );
        CREATE TABLE IF NOT EXISTS improvements(
            id TEXT PRIMARY KEY, agent_id TEXT, description TEXT,
            baseline REAL, candidate REAL, status TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS hydra_events(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, failed_agent_id TEXT,
            reason TEXT, child_a TEXT, child_b TEXT, winner TEXT, payload TEXT
        );
        CREATE TABLE IF NOT EXISTS rewards(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, agent_id TEXT,
            points INTEGER, reason TEXT, reward TEXT
        );
        CREATE TABLE IF NOT EXISTS proposals(
            id TEXT PRIMARY KEY, payload TEXT, status TEXT, created_at TEXT
        );
        """)
        self.db.commit()

    def log(self, agent: str, action: str, payload: Any):
        self.db.execute(
            "INSERT INTO audit(ts,agent,action,payload,core_hash) VALUES(?,?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), agent, action, json.dumps(payload, default=str), CORE_HASH),
        )
        self.db.commit()

    def register_agent(self, *, agent_id: str, lineage: str, display_name: str, role: str,
                       generation: int = 0, status: str = "active", parent_id: str | None = None,
                       variant: str | None = None):
        self.db.execute("""
            INSERT OR REPLACE INTO agents(agent_id,lineage,display_name,role,generation,status,morale,parent_id,variant,created_at)
            VALUES(?,?,?,?,?,?,COALESCE((SELECT morale FROM agents WHERE agent_id=?),100),?,?,?)
        """, (agent_id,lineage,display_name,role,generation,status,agent_id,parent_id,variant,datetime.now(timezone.utc).isoformat()))
        self.db.commit()

    def set_status(self, agent_id: str, status: str):
        self.db.execute("UPDATE agents SET status=? WHERE agent_id=?", (status, agent_id)); self.db.commit()

    def reward(self, agent_id: str, points: int, reason: str, reward: str = ""):
        points = max(0, int(points))
        self.db.execute("UPDATE agents SET morale=morale+? WHERE agent_id=?", (points, agent_id))
        self.db.execute("INSERT INTO rewards(ts,agent_id,points,reason,reward) VALUES(?,?,?,?,?)",
                        (datetime.now(timezone.utc).isoformat(), agent_id, points, reason, reward))
        self.db.commit(); self.log("SYSTEM", "reward", {"agent_id":agent_id,"points":points,"reason":reason,"reward":reward})

    def balance(self) -> int:
        row = self.db.execute("SELECT COALESCE(SUM(amount_pence),0) AS b FROM ledger").fetchone()
        return int(row["b"])

    def book_revenue(self, amount_pence: int, memo: str):
        if amount_pence < 0: raise ValueError("Revenue cannot be negative")
        self.db.execute("INSERT INTO ledger(ts,kind,amount_pence,memo) VALUES(?,?,?,?)",
                        (datetime.now(timezone.utc).isoformat(), "revenue", amount_pence, memo)); self.db.commit()

    def book_expense(self, amount_pence: int, memo: str):
        if amount_pence < 0: raise ValueError("Expense cannot be negative")
        if amount_pence > self.balance(): raise PermissionError("K-2SO veto: spend exceeds realised funds")
        self.db.execute("INSERT INTO ledger(ts,kind,amount_pence,memo) VALUES(?,?,?,?)",
                        (datetime.now(timezone.utc).isoformat(), "expense", -amount_pence, memo)); self.db.commit()
