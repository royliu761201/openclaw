#!/usr/bin/env python3
"""
SSoT Consolidation Script — Restores workspace/projects_core from GPU cold storage.

Usage:
    python3 ssot_consolidate.py                          # Audit all projects (dry-run)
    python3 ssot_consolidate.py --restore                # Restore all degraded projects
    python3 ssot_consolidate.py --restore --project X    # Restore specific project
    python3 ssot_consolidate.py --push-cold              # Push SSoT -> Server 03 cold storage

SSoT: ~/workspace/projects_core/<PROJECT>/
GPU:  gpu:/jhdx0003008/workspace/projects_core/<PROJECT>/
Cold: 03:/Users/roy-003/cold_storage/<PROJECT>/

Excludes (never pulled to Mac): *.npz *.h5 *.pt *.ckpt *.pth *.npy wandb/ __pycache__/ .git/
                                 data/raw/ data/processed/ results/checkpoints/
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

LOCAL_BASE = Path.home() / "workspace" / "projects_core"
GPU_BASE = "gpu:/jhdx0003008/workspace/projects_core"
COLD_BASE = "03:/Users/roy-003/cold_storage"

# Files/dirs that are intermediate artifacts — never pull to Mac SSoT
EXCLUDE_PATTERNS = [
    "*.npz", "*.h5", "*.pt", "*.ckpt", "*.pth", "*.npy",
    "wandb/", "__pycache__/", ".git/",
    "data/raw/", "data/processed/", "data/usyd_benchmark/",
    "data/benchmarks/", "results/checkpoints/", "results/mta_task_*/",
]

# Core NeurIPS projects to track
CORE_PROJECTS = [
    "FoveaCNO", "RicciPruning", "TopoDiffract", "CliffFormer",
    "DreamNash", "EMG_FacialNerve", "TopoTME", "TumorOperator",
    "PhysPromoFM", "L_TTT", "CaLaM", "PESSO", "PhysDiff",
    "Frenet", "S-FlashAttention", "TopoHeal", "RecSys_GDE",
]


def count_py_files(path: Path) -> int:
    if not path.exists():
        return 0
    result = subprocess.run(
        ["find", str(path), "-type", "f", "-name", "*.py"],
        capture_output=True, text=True
    )
    return len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0


def get_dir_size(path: Path) -> str:
    if not path.exists():
        return "0"
    result = subprocess.run(
        ["du", "-sh", str(path)], capture_output=True, text=True
    )
    return result.stdout.split()[0] if result.stdout else "0"


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    result = subprocess.run(
        ["find", str(path), "-type", "f"],
        capture_output=True, text=True
    )
    return len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0


def gpu_count_py(project: str) -> int:
    result = subprocess.run(
        ["ssh", "gpu", f'find /jhdx0003008/workspace/projects_core/{project} -type f -name "*.py" 2>/dev/null | wc -l'],
        capture_output=True, text=True, timeout=15
    )
    return int(result.stdout.strip()) if result.stdout.strip() else 0


def audit(projects: list[str]) -> list[dict]:
    """Audit local vs GPU project health."""
    print(f"{'Project':<20} {'Local.py':>9} {'GPU.py':>7} {'Status':>10} {'Size':>8}")
    print("-" * 60)
    results = []
    for proj in projects:
        local_path = LOCAL_BASE / proj
        local_py = count_py_files(local_path)
        try:
            gpu_py = gpu_count_py(proj)
        except Exception:
            gpu_py = -1

        if not local_path.exists():
            status = "❌ MISSING"
        elif local_py == 0:
            status = "❌ EMPTY"
        elif gpu_py > 0 and local_py < gpu_py * 0.5:
            status = "⚠️ DEGRADED"
        else:
            status = "✅ OK"

        size = get_dir_size(local_path)
        print(f"{proj:<20} {local_py:>9} {gpu_py:>7} {status:>10} {size:>8}")
        results.append({
            "project": proj,
            "local_py": local_py,
            "gpu_py": gpu_py,
            "status": status,
            "size": size,
        })
    return results


def restore_project(project: str, dry_run: bool = False):
    """Restore a project from GPU to local SSoT (code-only, no heavy artifacts)."""
    local_path = LOCAL_BASE / project
    gpu_path = f"{GPU_BASE}/{project}/"

    excludes = []
    for pat in EXCLUDE_PATTERNS:
        excludes.extend(["--exclude", pat])

    # Use high-throughput flags for direct connect (disable compression, use fast cipher)
    rsync_flags = ["-av", "-e", "ssh -c aes128-gcm@openssh.com -o Compression=no"]
    cmd = ["rsync"] + rsync_flags + ["--ignore-times"] + excludes + [gpu_path, str(local_path) + "/"]

    if dry_run:
        cmd.insert(1, "--dry-run")

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}Restoring {project}...")
    print(f"  Command: {' '.join(cmd[:6])}... {gpu_path} -> {local_path}/")
    result = subprocess.run(cmd, timeout=300)
    if result.returncode == 0:
        new_py = count_py_files(local_path)
        print(f"  ✅ {project} restored: {new_py} .py files")
    else:
        print(f"  ❌ {project} restore FAILED (exit code {result.returncode})")


def push_cold(project: str):
    """Push local SSoT to Server 03 cold storage."""
    local_path = LOCAL_BASE / project
    cold_path = f"{COLD_BASE}/{project}/"

    excludes = []
    for pat in EXCLUDE_PATTERNS:
        excludes.extend(["--exclude", pat])

    # Use high-throughput flags for direct connect (disable compression, use fast cipher)
    rsync_flags = ["-av", "-e", "ssh -c aes128-gcm@openssh.com -o Compression=no"]
    cmd = ["rsync"] + rsync_flags + excludes + [str(local_path) + "/", cold_path]
    print(f"\nPushing {project} -> 03 cold storage...")
    result = subprocess.run(cmd, timeout=300)
    if result.returncode == 0:
        print(f"  ✅ {project} synced to 03")
    else:
        print(f"  ❌ {project} push FAILED (exit code {result.returncode})")


def push_gpu(project: str):
    """Push local SSoT to GPU cluster."""
    local_path = LOCAL_BASE / project
    gpu_path = f"{GPU_BASE}/{project}/"

    excludes = []
    for pat in EXCLUDE_PATTERNS:
        excludes.extend(["--exclude", pat])

    # Use high-throughput flags for direct connect (disable compression, use fast cipher)
    rsync_flags = ["-av", "-e", "ssh -c aes128-gcm@openssh.com -o Compression=no"]
    cmd = ["rsync"] + rsync_flags + excludes + [str(local_path) + "/", gpu_path]
    print(f"\nPushing {project} -> GPU cluster...")
    result = subprocess.run(cmd, timeout=300)
    if result.returncode == 0:
        print(f"  ✅ {project} synced to GPU")
    else:
        print(f"  ❌ {project} sync FAILED (exit code {result.returncode})")


def main():
    parser = argparse.ArgumentParser(description="SSoT Consolidation: Restore workspace from GPU/Cold")
    parser.add_argument("--restore", action="store_true", help="Restore degraded projects from GPU")
    parser.add_argument("--push-cold", action="store_true", help="Push SSoT to Server 03 cold storage")
    parser.add_argument("--push-gpu", action="store_true", help="Push SSoT to GPU cluster")
    parser.add_argument("--project", type=str, help="Target a specific project (default: all)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be transferred")
    parser.add_argument("--all", action="store_true", help="Include all projects, not just degraded ones")
    args = parser.parse_args()

    projects = [args.project] if args.project else CORE_PROJECTS

    print(f"=== SSoT Consolidation Audit — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")
    results = audit(projects)

    if args.restore:
        degraded = [r for r in results if "MISSING" in r["status"] or "EMPTY" in r["status"] or "DEGRADED" in r["status"]]
        targets = results if args.all else degraded
        if not targets:
            print("\n✅ All projects healthy — nothing to restore.")
            return
        print(f"\n--- Restoring {len(targets)} project(s) ---")
        for r in targets:
            restore_project(r["project"], dry_run=args.dry_run)

    if args.push_cold:
        for r in results:
            push_cold(r["project"])

    if args.push_gpu:
        for r in results:
            push_gpu(r["project"])

    # Write audit report
    report_path = LOCAL_BASE / "ssot_audit_report.json"
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
        }, f, indent=2, ensure_ascii=False)
    print(f"\n📋 Audit report saved: {report_path}")


if __name__ == "__main__":
    main()
