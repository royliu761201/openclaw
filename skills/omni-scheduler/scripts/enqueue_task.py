#!/usr/bin/env python3
"""Append immutable scheduler intents into the PESSO CQRS event log."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


WORKSPACE_ROOT = Path("/Users/roy-jd/workspace")
PESSO_ROOT = WORKSPACE_ROOT / "projects_core" / "PESSO"
if str(PESSO_ROOT) not in sys.path:
    sys.path.insert(0, str(PESSO_ROOT))

from src.cqrs.event_store import (  # noqa: E402
    DEFAULT_EXPERIMENT_QUEUE,
    DEFAULT_OMNI_QUEUE,
    MatrixIntentEventStore,
)
from src.cqrs.reducer import DEFAULT_DB_PATH, PESSOStateReducer  # noqa: E402


def enqueue() -> None:
    parser = argparse.ArgumentParser(description="Append a task.enqueued intent into the PESSO CQRS backend")
    parser.add_argument("--project", required=True, help="Project name")
    parser.add_argument("--entry", required=True, help="Entry script path")
    parser.add_argument("--target", choices=["local", "kaggle_a", "kaggle_b"], default="local")
    parser.add_argument("--datasets", nargs="*", default=[], help="Optional dataset mounts for Kaggle payloads")
    parser.add_argument("--queue-name", choices=[DEFAULT_OMNI_QUEUE, DEFAULT_EXPERIMENT_QUEUE], default=None)
    parser.add_argument("--command", default=None)
    parser.add_argument("--dir", dest="directory", default=None)
    parser.add_argument("--env", default=None)
    parser.add_argument("--group", default=None)
    parser.add_argument("--task-id", default=None, help="Explicit external task identifier")
    parser.add_argument("--actor", default="enqueue_task.py")
    parser.add_argument("--status", default="PENDING")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--log-path", default=None)
    args = parser.parse_args()

    queue_name = args.queue_name
    if queue_name is None:
        queue_name = DEFAULT_EXPERIMENT_QUEUE if args.command or args.directory or args.group else DEFAULT_OMNI_QUEUE

    payload: dict[str, object] = {}
    if args.target.startswith("kaggle"):
        payload["kaggle_payload"] = {
            "dataset_mounts": list(args.datasets),
            "secret_mounts": ["WANDB_API_KEY"],
            "gpu_type": "P100",
            "internet": True,
        }
    if args.env:
        payload["env"] = args.env

    event_store = MatrixIntentEventStore(log_path=args.log_path) if args.log_path else MatrixIntentEventStore()
    reducer = PESSOStateReducer(log_path=event_store.log_path, db_path=args.db_path)

    event = event_store.append_enqueue_intent(
        queue_name=queue_name,
        project=args.project,
        entry=args.entry,
        target=args.target,
        actor=args.actor,
        command=args.command,
        directory=args.directory,
        group_name=args.group,
        payload=payload,
        status=args.status,
        external_task_id=args.task_id,
    )
    reducer.refresh_projection()

    print(f"✅ Task [{args.project}] appended into [{queue_name}]")
    print(f"   Task Key: {event['task_key']}")
    print(f"   Intent ID: {event['intent_id']}")
    print(f"   Intent Log: {event_store.log_path}")
    print(f"   SQLite Projection: {Path(reducer.db_path)}")


if __name__ == "__main__":
    enqueue()
