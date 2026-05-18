from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .event_store import (
    DEFAULT_EXPERIMENT_QUEUE,
    DEFAULT_INTENT_LOG_PATH,
    DEFAULT_OMNI_QUEUE,
    MatrixIntentEventStore,
)


WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
PROJECTS_CORE_ROOT = WORKSPACE_ROOT / "projects_core"
DEFAULT_DB_PATH = PROJECTS_CORE_ROOT / ".scheduler_state" / "pesso_state.sqlite"


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _json_loads(payload: str | None) -> dict[str, Any]:
    if not payload:
        return {}
    data = json.loads(payload)
    return data if isinstance(data, dict) else {}


class PESSOStateReducer:
    """Deterministically replays append-only intents into a SQLite projection."""

    def __init__(
        self,
        log_path: str | Path = DEFAULT_INTENT_LOG_PATH,
        db_path: str | Path = DEFAULT_DB_PATH,
    ):
        self.event_store = MatrixIntentEventStore(log_path=log_path)
        self.log_path = self.event_store.log_path
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=10000")
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS intent_log (
                    seq INTEGER PRIMARY KEY,
                    intent_id TEXT NOT NULL UNIQUE,
                    intent_type TEXT NOT NULL,
                    task_key TEXT NOT NULL,
                    queue_name TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_intent_log_task_key
                ON intent_log(task_key, seq);

                CREATE TABLE IF NOT EXISTS task_projection (
                    task_key TEXT PRIMARY KEY,
                    queue_name TEXT NOT NULL,
                    project TEXT,
                    entry TEXT,
                    target TEXT,
                    command TEXT,
                    directory TEXT,
                    group_name TEXT,
                    status TEXT NOT NULL,
                    assigned_gpu TEXT,
                    lease_owner TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_intent_id TEXT NOT NULL,
                    state_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_task_projection_queue_status
                ON task_projection(queue_name, status, updated_at);
                """
            )

    def _default_task_state(self, *, task_key: str, queue_name: str, created_at: str) -> dict[str, Any]:
        return {
            "task_key": task_key,
            "queue_name": queue_name,
            "project": None,
            "entry": None,
            "target": None,
            "command": None,
            "directory": None,
            "group_name": None,
            "status": "PENDING",
            "assigned_gpu": None,
            "lease_owner": None,
            "start_time": None,
            "end_time": None,
            "created_at": created_at,
            "updated_at": created_at,
            "last_intent_id": "",
            "state": {},
        }

    def _status_for_intent(self, intent_type: str, payload: dict[str, Any], current_status: str) -> str:
        if payload.get("status"):
            return str(payload["status"])
        implicit = {
            "task.enqueued": "PENDING",
            "task.assigned": "ASSIGNED",
            "task.started": "RUNNING",
            "task.heartbeat": current_status,
            "task.completed": "COMPLETED",
            "task.failed": "FAILED",
            "task.cancelled": "CANCELLED",
            "task.reaped": "REAPED",
            "task.updated": current_status,
        }
        return implicit.get(intent_type, current_status)

    def _apply_intent(self, tasks: dict[str, dict[str, Any]], intent: dict[str, Any]) -> None:
        task_key = str(intent.get("task_key") or "").strip()
        if not task_key:
            return

        payload = intent.get("payload")
        if not isinstance(payload, dict):
            payload = {}

        queue_name = str(
            intent.get("queue_name")
            or payload.get("queue_name")
            or DEFAULT_EXPERIMENT_QUEUE
        )
        created_at = str(intent.get("created_at") or "")
        task = tasks.setdefault(
            task_key,
            self._default_task_state(task_key=task_key, queue_name=queue_name, created_at=created_at),
        )

        task["queue_name"] = queue_name
        task["updated_at"] = created_at or task["updated_at"]
        task["last_intent_id"] = str(intent.get("intent_id") or task["last_intent_id"])

        for field in ("project", "entry", "target", "command", "directory", "group_name"):
            if payload.get(field) is not None:
                task[field] = payload[field]

        if payload.get("assigned_gpu") is not None:
            task["assigned_gpu"] = str(payload["assigned_gpu"])
        if payload.get("lease_owner") is not None:
            task["lease_owner"] = str(payload["lease_owner"])

        task["status"] = self._status_for_intent(str(intent.get("intent_type") or ""), payload, str(task["status"]))

        if payload.get("start_time") is not None:
            task["start_time"] = str(payload["start_time"])
        elif task["status"] == "RUNNING" and task["start_time"] is None:
            task["start_time"] = created_at

        if payload.get("end_time") is not None:
            task["end_time"] = str(payload["end_time"])
        elif task["status"] in {"COMPLETED", "FAILED", "CANCELLED", "REAPED"}:
            task["end_time"] = created_at

        task_state = task["state"]
        task_state.update(payload)
        task_state["queue_name"] = queue_name
        task_state["task_key"] = task_key
        task_state["last_intent_type"] = intent.get("intent_type")
        task_state["updated_at"] = task["updated_at"]

    def refresh_projection(self) -> dict[str, int]:
        intents = self.event_store.read_intents()
        tasks: dict[str, dict[str, Any]] = {}
        for intent in intents:
            self._apply_intent(tasks, intent)

        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM intent_log")
            for seq, intent in enumerate(intents, start=1):
                conn.execute(
                    """
                    INSERT INTO intent_log(
                        seq, intent_id, intent_type, task_key, queue_name, actor, created_at, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        seq,
                        str(intent.get("intent_id") or ""),
                        str(intent.get("intent_type") or ""),
                        str(intent.get("task_key") or ""),
                        str(intent.get("queue_name") or DEFAULT_EXPERIMENT_QUEUE),
                        str(intent.get("actor") or "unknown"),
                        str(intent.get("created_at") or ""),
                        _json_dumps(intent.get("payload") if isinstance(intent.get("payload"), dict) else {}),
                    ),
                )

            conn.execute("DELETE FROM task_projection")
            for task in sorted(tasks.values(), key=lambda row: (row["queue_name"], row["created_at"], row["task_key"])):
                conn.execute(
                    """
                    INSERT INTO task_projection(
                        task_key, queue_name, project, entry, target, command, directory, group_name,
                        status, assigned_gpu, lease_owner, start_time, end_time,
                        created_at, updated_at, last_intent_id, state_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        task["task_key"],
                        task["queue_name"],
                        task["project"],
                        task["entry"],
                        task["target"],
                        task["command"],
                        task["directory"],
                        task["group_name"],
                        task["status"],
                        task["assigned_gpu"],
                        task["lease_owner"],
                        task["start_time"],
                        task["end_time"],
                        task["created_at"],
                        task["updated_at"],
                        task["last_intent_id"],
                        _json_dumps(task["state"]),
                    ),
                )
            conn.commit()

        return {"intent_count": len(intents), "task_count": len(tasks)}

    def get_projection(self, queue_name: str | None = None, status: str | None = None) -> dict[str, Any]:
        query = "SELECT * FROM task_projection"
        clauses: list[str] = []
        params: list[Any] = []
        if queue_name:
            clauses.append("queue_name = ?")
            params.append(queue_name)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY queue_name, created_at, task_key"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()

        tasks: list[dict[str, Any]] = []
        for row in rows:
            state = _json_loads(row["state_json"])
            task = {
                "id": row["task_key"],
                "task_key": row["task_key"],
                "queue_name": row["queue_name"],
                "project": row["project"],
                "entry": row["entry"],
                "target": row["target"],
                "command": row["command"],
                "directory": row["directory"],
                "group_name": row["group_name"],
                "status": row["status"],
                "assigned_gpu": row["assigned_gpu"],
                "lease_owner": row["lease_owner"],
                "start_time": row["start_time"],
                "end_time": row["end_time"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "last_intent_id": row["last_intent_id"],
            }
            for key, value in state.items():
                if key not in task:
                    task[key] = value
            tasks.append(task)

        return {
            "tasks": tasks,
            "queue_name": queue_name,
            "status_filter": status,
            "db_path": str(self.db_path),
            "intent_log_path": str(self.log_path),
        }

    def get_experiment_queue_projection(self) -> dict[str, Any]:
        return self.get_projection(queue_name=DEFAULT_EXPERIMENT_QUEUE)

    def get_matrix_state_projection(self) -> dict[str, Any]:
        projection = self.get_projection()
        return {
            task["task_key"]: {
                "status": task["status"],
                "assigned_gpu": task.get("assigned_gpu"),
                "updated_at": task.get("updated_at"),
                "last_intent_id": task.get("last_intent_id"),
            }
            for task in projection["tasks"]
        }
