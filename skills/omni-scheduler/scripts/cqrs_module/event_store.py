from __future__ import annotations

import contextlib
import datetime as dt
import json
import os
import uuid
from pathlib import Path
from typing import Any, Iterator

try:
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None


WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
PROJECTS_CORE_ROOT = WORKSPACE_ROOT / "projects_core"
DEFAULT_INTENT_LOG_PATH = PROJECTS_CORE_ROOT / "matrix_intent.jsonl"
DEFAULT_LOCK_PATH = PROJECTS_CORE_ROOT / ".scheduler_state" / "matrix_intent.lock"

DEFAULT_OMNI_QUEUE = "omni_tracker"
DEFAULT_EXPERIMENT_QUEUE = "experiment_scheduler"


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


class MatrixIntentEventStore:
    """Append-only JSONL event store for scheduler intents."""

    def __init__(
        self,
        log_path: str | Path = DEFAULT_INTENT_LOG_PATH,
        lock_path: str | Path = DEFAULT_LOCK_PATH,
    ):
        self.log_path = Path(log_path)
        self.lock_path = Path(lock_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.touch()

    @contextlib.contextmanager
    def _append_lock(self) -> Iterator[None]:
        with self.lock_path.open("a+", encoding="utf-8") as handle:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                if fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def build_task_key(
        self,
        project: str,
        queue_name: str = DEFAULT_EXPERIMENT_QUEUE,
        external_task_id: str | None = None,
    ) -> str:
        if external_task_id:
            return str(external_task_id)
        project_slug = str(project).strip().replace(" ", "_") or "task"
        return f"{queue_name}:{project_slug}:{uuid.uuid4().hex[:12]}"

    def append_intent(
        self,
        *,
        intent_type: str,
        task_key: str,
        payload: dict[str, Any],
        actor: str,
        queue_name: str = DEFAULT_EXPERIMENT_QUEUE,
    ) -> dict[str, Any]:
        event = {
            "intent_id": uuid.uuid4().hex,
            "intent_type": str(intent_type),
            "task_key": str(task_key),
            "queue_name": str(queue_name),
            "actor": str(actor),
            "created_at": _utc_now(),
            "payload": dict(payload),
        }
        line = json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
        with self._append_lock():
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(line)
                handle.flush()
                os.fsync(handle.fileno())
        return event

    def append_enqueue_intent(
        self,
        *,
        queue_name: str,
        project: str,
        entry: str,
        target: str,
        actor: str,
        command: str | None = None,
        directory: str | None = None,
        group_name: str | None = None,
        payload: dict[str, Any] | None = None,
        status: str = "PENDING",
        external_task_id: str | None = None,
    ) -> dict[str, Any]:
        task_key = self.build_task_key(project, queue_name=queue_name, external_task_id=external_task_id)
        event_payload = {
            "project": project,
            "entry": entry,
            "target": target,
            "command": command,
            "directory": directory,
            "group_name": group_name,
            "status": status,
            "external_task_id": external_task_id or task_key,
        }
        if payload:
            event_payload.update(payload)
        return self.append_intent(
            intent_type="task.enqueued",
            task_key=task_key,
            payload=event_payload,
            actor=actor,
            queue_name=queue_name,
        )

    def read_intents(self) -> list[dict[str, Any]]:
        intents: list[dict[str, Any]] = []
        if not self.log_path.exists():
            return intents

        with self.log_path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, start=1):
                raw = line.strip()
                if not raw:
                    continue
                data = json.loads(raw)
                if not isinstance(data, dict):
                    raise ValueError(f"Intent log line {line_no} is not a JSON object.")
                intents.append(data)
        return intents
