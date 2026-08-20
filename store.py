from __future__ import annotations

import json
import os
import sqlite3
import uuid
from dataclasses import asdict, is_dataclass
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
        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
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
        CREATE TABLE IF NOT EXISTS sales(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT UNIQUE,
            proposal_id TEXT,
            gross_pence INTEGER,
            fee_pence INTEGER,
            net_pence INTEGER,
            ts TEXT
        );
        CREATE TABLE IF NOT EXISTS expenses(
            id TEXT PRIMARY KEY,
            date TEXT,
            category TEXT,
            amount_pence INTEGER,
            description TEXT,
            receipt_ref TEXT,
            justification TEXT,
            approved_by TEXT,
            approved INTEGER DEFAULT 0,
            created_at TEXT
        );
        """)
        self.db.commit()

    @staticmethod
    def _coerce_ts(ts: datetime | str | None = None) -> str:
        if ts is None:
            dt = datetime.now(timezone.utc)
        elif isinstance(ts, str):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            dt = ts
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()

    def log(self, agent: str, action: str, payload: Any):
        self.db.execute(
            "INSERT INTO audit(ts,agent,action,payload,core_hash) VALUES(?,?,?,?,?)",
            (self._coerce_ts(), agent, action, json.dumps(payload, default=str), CORE_HASH),
        )
        self.db.commit()

    def register_agent(self, *, agent_id: str, lineage: str, display_name: str, role: str,
                       generation: int = 0, status: str = "active", parent_id: str | None = None,
                       variant: str | None = None):
        self.db.execute("""
            INSERT OR REPLACE INTO agents(agent_id,lineage,display_name,role,generation,status,morale,parent_id,variant,created_at)
            VALUES(?,?,?,?,?,?,COALESCE((SELECT morale FROM agents WHERE agent_id=?),100),?,?,?)
        """, (agent_id,lineage,display_name,role,generation,status,agent_id,parent_id,variant,self._coerce_ts()))
        self.db.commit()

    def set_status(self, agent_id: str, status: str):
        self.db.execute("UPDATE agents SET status=? WHERE agent_id=?", (status, agent_id)); self.db.commit()

    def reward(self, agent_id: str, points: int, reason: str, reward: str = ""):
        points = max(0, int(points))
        self.db.execute("UPDATE agents SET morale=morale+? WHERE agent_id=?", (points, agent_id))
        self.db.execute("INSERT INTO rewards(ts,agent_id,points,reason,reward) VALUES(?,?,?,?,?)",
                        (self._coerce_ts(), agent_id, points, reason, reward))
        self.db.commit(); self.log("SYSTEM", "reward", {"agent_id":agent_id,"points":points,"reason":reason,"reward":reward})

    def agents(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.db.execute(
                "SELECT agent_id, display_name, role, generation, status, morale FROM agents ORDER BY display_name"
            ).fetchall()
        ]

    def balance(self) -> int:
        row = self.db.execute("SELECT COALESCE(SUM(amount_pence),0) AS b FROM ledger").fetchone()
        return int(row["b"])

    def book_revenue(self, amount_pence: int, memo: str, ts: datetime | str | None = None):
        if amount_pence < 0: raise ValueError("Revenue cannot be negative")
        self.db.execute("INSERT INTO ledger(ts,kind,amount_pence,memo) VALUES(?,?,?,?)",
                        (self._coerce_ts(ts), "revenue", amount_pence, memo)); self.db.commit()

    def book_expense(self, amount_pence: int, memo: str, ts: datetime | str | None = None):
        if amount_pence < 0: raise ValueError("Expense cannot be negative")
        if amount_pence > self.balance(): raise PermissionError("K-2SO veto: spend exceeds realised funds")
        self.db.execute("INSERT INTO ledger(ts,kind,amount_pence,memo) VALUES(?,?,?,?)",
                        (self._coerce_ts(ts), "expense", -amount_pence, memo)); self.db.commit()

    def save_proposal(self, proposal: Any, status: str):
        payload = asdict(proposal) if is_dataclass(proposal) else proposal
        proposal_id = payload["id"]
        created_at = self.db.execute(
            "SELECT created_at FROM proposals WHERE id=?",
            (proposal_id,),
        ).fetchone()
        ts = created_at["created_at"] if created_at else self._coerce_ts()
        self.db.execute(
            "INSERT OR REPLACE INTO proposals(id,payload,status,created_at) VALUES(?,?,?,?)",
            (proposal_id, json.dumps(payload, default=str), status, ts),
        )
        self.db.commit()

    def record_sale(
        self,
        proposal_id: str,
        gross_pence: int,
        fee_pence: int = 0,
        external_id: str | None = None,
        ts: datetime | str | None = None,
    ) -> dict[str, Any]:
        gross_pence = int(gross_pence)
        fee_pence = int(fee_pence)
        if gross_pence < 0 or fee_pence < 0:
            raise ValueError("Sale amounts cannot be negative")
        net_pence = max(0, gross_pence - fee_pence)
        external_id = external_id or str(uuid.uuid4())
        try:
            sale_ts = self._coerce_ts(ts)
            with self.db:
                self.db.execute(
                    "INSERT INTO sales(external_id,proposal_id,gross_pence,fee_pence,net_pence,ts) VALUES(?,?,?,?,?,?)",
                    (external_id, proposal_id, gross_pence, fee_pence, net_pence, sale_ts),
                )
                self.db.execute(
                    "INSERT INTO ledger(ts,kind,amount_pence,memo) VALUES(?,?,?,?)",
                    (sale_ts, "revenue", net_pence, f"sale:{proposal_id}"),
                )
                self.db.execute(
                    "INSERT INTO audit(ts,agent,action,payload,core_hash) VALUES(?,?,?,?,?)",
                    (
                        sale_ts,
                        "TARS",
                        "sale_recorded",
                        json.dumps(
                            {
                                "proposal_id": proposal_id,
                                "gross_pence": gross_pence,
                                "fee_pence": fee_pence,
                                "net_pence": net_pence,
                                "external_id": external_id,
                            },
                            default=str,
                        ),
                        CORE_HASH,
                    ),
                )
        except sqlite3.IntegrityError:
            return {"status": "duplicate", "external_id": external_id}
        return {"status": "recorded", "net_pence": net_pence, "external_id": external_id}

    def proposals(self) -> list[dict[str, Any]]:
        rows = self.db.execute(
            "SELECT id, payload, status, created_at FROM proposals ORDER BY created_at DESC"
        ).fetchall()
        results: list[dict[str, Any]] = []
        for row in rows:
            payload = json.loads(row["payload"])
            payload.update({"status": row["status"], "created_at": row["created_at"]})
            results.append(payload)
        return results

    def sales(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.db.execute(
                "SELECT external_id, proposal_id, gross_pence, fee_pence, net_pence, ts FROM sales ORDER BY ts DESC"
            ).fetchall()
        ]

    def ledger_entries(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.db.execute(
                "SELECT ts, kind, amount_pence, memo FROM ledger ORDER BY ts DESC"
            ).fetchall()
        ]

    def audit_events(self, limit: int = 200) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.db.execute(
                "SELECT ts, agent, action, payload FROM audit ORDER BY ts DESC LIMIT ?",
                (limit,),
            ).fetchall()
        ]

    def reward_events(self) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in self.db.execute(
                "SELECT ts, agent_id, points, reason, reward FROM rewards ORDER BY ts DESC"
            ).fetchall()
        ]

    def gross_revenue(self) -> int:
        row = self.db.execute(
            "SELECT COUNT(*) AS c, COALESCE(SUM(gross_pence),0) AS r FROM sales"
        ).fetchone()
        if int(row["c"]):
            return int(row["r"])
        row = self.db.execute(
            "SELECT COALESCE(SUM(amount_pence),0) AS r FROM ledger WHERE kind='revenue'"
        ).fetchone()
        return int(row["r"])

    def add_expense_log(self, *, expense_id: str, date: str, category: str, amount_pence: int,
                        description: str, receipt_ref: str, justification: str,
                        approved_by: str, approved: bool) -> None:
        self.db.execute(
            """INSERT INTO expenses(id,date,category,amount_pence,description,receipt_ref,
               justification,approved_by,approved,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (expense_id, date, category, amount_pence, description, receipt_ref, justification,
             approved_by, int(approved), datetime.now(timezone.utc).isoformat()),
        )
        self.db.commit()

    def list_expense_logs(self, approved_only: bool = True) -> list[dict]:
        q = "SELECT * FROM expenses"
        if approved_only:
            q += " WHERE approved=1"
        q += " ORDER BY date"
        return [dict(row) for row in self.db.execute(q).fetchall()]

    def total_approved_expenses_pence(self) -> int:
        row = self.db.execute(
            "SELECT COALESCE(SUM(amount_pence),0) AS t FROM expenses WHERE approved=1"
        ).fetchone()
        return int(row["t"])
