from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from staytrace.core.models import ChangeFinding, ClaimAnalysis, Observation, Inspection, now_iso


class Store:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init()

    def _init(self) -> None:
        self.conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS inspections (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                room_name TEXT NOT NULL,
                type TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS media (
                id TEXT PRIMARY KEY,
                inspection_id TEXT NOT NULL,
                path TEXT NOT NULL,
                original_name TEXT NOT NULL,
                sha256 TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS observations (
                id TEXT PRIMARY KEY,
                inspection_id TEXT NOT NULL,
                media_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS findings (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS claims (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS benchmarks (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                operation TEXT NOT NULL,
                latency_ms REAL NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    def create_project(self, name: str) -> str:
        pid = uuid.uuid4().hex
        self.conn.execute("INSERT INTO projects VALUES (?, ?, ?)", (pid, name, now_iso()))
        self.conn.commit()
        return pid

    def list_projects(self) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()

    def create_inspection(self, project_id: str, room_name: str, kind: str, notes: str = "") -> str:
        iid = uuid.uuid4().hex
        self.conn.execute(
            "INSERT INTO inspections VALUES (?, ?, ?, ?, ?, ?)",
            (iid, project_id, room_name, kind, now_iso(), notes),
        )
        self.conn.commit()
        return iid

    def add_media(
        self,
        inspection_id: str,
        path: str,
        original_name: str,
        sha256: str,
        width: int,
        height: int,
    ) -> str:
        mid = uuid.uuid4().hex
        self.conn.execute(
            "INSERT INTO media VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (mid, inspection_id, path, original_name, sha256, width, height, now_iso()),
        )
        self.conn.commit()
        return mid

    def add_observation(self, observation: Observation) -> str:
        oid = uuid.uuid4().hex
        self.conn.execute(
            "INSERT INTO observations VALUES (?, ?, ?, ?, ?)",
            (
                oid,
                observation.inspection_id,
                observation.image_id,
                observation.model_dump_json(),
                observation.created_at,
            ),
        )
        self.conn.commit()
        return oid

    def add_finding(self, project_id: str, finding: ChangeFinding) -> str:
        fid = uuid.uuid4().hex
        self.conn.execute(
            "INSERT INTO findings VALUES (?, ?, ?, ?)",
            (fid, project_id, finding.model_dump_json(), now_iso()),
        )
        self.conn.commit()
        return fid

    def add_claim(self, project_id: str, claim: ClaimAnalysis) -> str:
        cid = uuid.uuid4().hex
        self.conn.execute(
            "INSERT INTO claims VALUES (?, ?, ?, ?)",
            (cid, project_id, claim.model_dump_json(), now_iso()),
        )
        self.conn.commit()
        return cid

    def add_benchmark(self, project_id: str | None, operation: str, latency_ms: float, metadata: dict[str, Any]) -> None:
        bid = uuid.uuid4().hex
        self.conn.execute(
            "INSERT INTO benchmarks VALUES (?, ?, ?, ?, ?, ?)",
            (bid, project_id, operation, float(latency_ms), json.dumps(metadata), now_iso()),
        )
        self.conn.commit()

    def get_inspections(self, project_id: str, kind: str | None = None) -> list[sqlite3.Row]:
        if kind:
            return self.conn.execute(
                "SELECT * FROM inspections WHERE project_id=? AND type=? ORDER BY captured_at DESC",
                (project_id, kind),
            ).fetchall()
        return self.conn.execute(
            "SELECT * FROM inspections WHERE project_id=? ORDER BY captured_at DESC",
            (project_id,),
        ).fetchall()

    def get_media(self, inspection_id: str) -> list[sqlite3.Row]:
        return self.conn.execute("SELECT * FROM media WHERE inspection_id=? ORDER BY created_at", (inspection_id,)).fetchall()

    def get_observations(self, inspection_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM observations WHERE inspection_id=? ORDER BY created_at", (inspection_id,)).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def get_findings(self, project_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM findings WHERE project_id=? ORDER BY created_at", (project_id,)).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def get_claims(self, project_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute("SELECT * FROM claims WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
        return [json.loads(r["payload"]) for r in rows]

    def get_benchmarks(self, project_id: str | None) -> list[sqlite3.Row]:
        if project_id:
            return self.conn.execute("SELECT * FROM benchmarks WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
        return self.conn.execute("SELECT * FROM benchmarks ORDER BY created_at DESC").fetchall()

    def close(self) -> None:
        self.conn.close()
