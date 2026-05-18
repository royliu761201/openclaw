#!/usr/bin/env python3
"""Read the SQLite projection, then append scheduler intents back into the event log."""

from __future__ import annotations

import argparse
import os
import socket
import sys
from pathlib import Path


WORKSPACE_ROOT = Path("/Users/roy-jd/workspace")
PESSO_ROOT = WORKSPACE_ROOT / "projects_core" / "PESSO"
if str(PESSO_ROOT) not in sys.path:
    sys.path.insert(0, str(PESSO_ROOT))

from src.cqrs.event_store import (  # noqa: E402
    DEFAULT_EXPERIMENT_QUEUE,
    MatrixIntentEventStore,
)
from src.cqrs.reducer import DEFAULT_DB_PATH, PESSOStateReducer  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Projection-driven scheduler for the PESSO CQRS backend")
    parser.add_argument("--queue-name", default=DEFAULT_EXPERIMENT_QUEUE)
    parser.add_argument("--gpu", default=None, help="GPU identifier recorded into the assignment intent")
    parser.add_argument("--lease-owner", default=None, help="Lease owner tag recorded into assignment intents")
    parser.add_argument("--limit", type=int, default=1, help="Maximum number of pending tasks to claim")
    parser.add_argument("--status", default="RUNNING", help="Status written by the assignment intent")
    parser.add_argument("--dry-run", action="store_true", help="Only show which tasks would be claimed")
    parser.add_argument("--actor", default="auto_scheduler.py")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH))
    parser.add_argument("--log-path", default=None)
    args = parser.parse_args()

    event_store = MatrixIntentEventStore(log_path=args.log_path) if args.log_path else MatrixIntentEventStore()
    reducer = PESSOStateReducer(log_path=event_store.log_path, db_path=args.db_path)
    reducer.refresh_projection()

    projection = reducer.get_projection(queue_name=args.queue_name, status="PENDING")
    pending = projection.get("tasks", [])
    selected = pending[: max(0, int(args.limit))]

    if not selected:
        print("No pending tasks available.")
        print(f"Projection DB: {projection.get('db_path')}")
        return

    lease_owner = args.lease_owner or f"{socket.gethostname()}:{os.getpid()}"
    print(f"Queue: {args.queue_name}")
    print(f"Pending tasks available: {len(pending)}")
    for task in selected:
        print(f"  - {task['task_key']} ({task.get('project')})")

    if args.dry_run:
        print("Dry-run only. No intents appended.")
        return

    for task in selected:
        payload = {
            "status": args.status,
            "assigned_gpu": args.gpu,
            "lease_owner": lease_owner,
        }
        event_store.append_intent(
            intent_type="task.assigned",
            task_key=str(task["task_key"]),
            payload=payload,
            actor=args.actor,
            queue_name=args.queue_name,
        )

    result = reducer.refresh_projection()
    print(f"Appended {len(selected)} assignment intent(s).")
    print(f"Intent Count: {result['intent_count']}")
    print(f"Projected Tasks: {result['task_count']}")
    print(f"Projection DB: {reducer.db_path}")


if __name__ == "__main__":
    main()
