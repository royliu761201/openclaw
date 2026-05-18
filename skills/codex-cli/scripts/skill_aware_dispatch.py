#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterable, Sequence

SCRIPT_PATH = Path(__file__).resolve()
DEFAULT_WORKSPACE_ROOT = Path.home() / "workspace"
DEFAULT_OPENCLAW_ROOT = Path.home() / "openclaw"
SYSTEM_LAW_FILES = (
    "06_DATA_GOVERNANCE_LAW.md",
    "07_HARDWARE_NETWORK_LAW.md",
)


class DispatchError(RuntimeError):
    """Raised when dispatcher setup or execution cannot continue."""


def log(level: str, message: str) -> None:
    print(f"[ARR-{level}] {message}", file=sys.stderr)


def unique_paths(paths: Iterable[Path]) -> list[Path]:
    resolved: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        candidate = path.expanduser()
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        resolved.append(candidate)
    return resolved


def choose_path(
    label: str,
    candidates: Iterable[Path],
    predicate: Callable[[Path], bool],
) -> Path:
    unique_candidates = unique_paths(candidates)
    for candidate in unique_candidates:
        if predicate(candidate):
            return candidate

    if unique_candidates:
        fallback = unique_candidates[0]
        log("WARN", f"Unable to auto-detect {label}; falling back to {fallback}")
        return fallback

    raise DispatchError(f"No candidates available while resolving {label}.")


def resolve_openclaw_root() -> Path:
    env_value = os.environ.get("OPENCLAW_ROOT")
    candidates: list[Path] = []
    if env_value:
        candidates.append(Path(env_value))

    for parent in SCRIPT_PATH.parents:
        if (parent / "skills").is_dir() and (parent / "docs").is_dir():
            candidates.append(parent)

    candidates.append(DEFAULT_OPENCLAW_ROOT)
    return choose_path(
        "OpenClaw root",
        candidates,
        lambda path: (path / "skills").is_dir() and (path / "docs").is_dir(),
    )


def resolve_workspace_root(openclaw_root: Path) -> Path:
    env_value = os.environ.get("WORKSPACE_ROOT")
    candidates: list[Path] = []
    if env_value:
        candidates.append(Path(env_value))

    candidates.extend(
        [
            DEFAULT_WORKSPACE_ROOT,
            openclaw_root.parent / "workspace",
        ]
    )

    return choose_path(
        "workspace root",
        candidates,
        lambda path: (path / ".clinerules").is_file()
        or (path / "docs" / "system_core").is_dir(),
    )


def read_text_file(path: Path) -> str | None:
    if not path.exists():
        log("WARN", f"Missing file: {path}")
        return None
    if not path.is_file():
        log("WARN", f"Expected a file but found something else: {path}")
        return None

    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        log("WARN", f"Failed to read {path}: {exc}")
        return None

    if not content:
        log("WARN", f"File is empty: {path}")
        return None

    return content


def missing_block(label: str, path: Path) -> str:
    return f"[ARR-MISSING] {label} unavailable: {path}"


def load_system_laws(system_core_dir: Path) -> str:
    log("INFO", f"Compiling global system laws from {system_core_dir}")
    compiled_laws: list[str] = []

    for filename in SYSTEM_LAW_FILES:
        law_path = system_core_dir / filename
        content = read_text_file(law_path)
        body = content if content is not None else missing_block("System law", law_path)
        compiled_laws.append(f"--- {filename} ---\n{body}")

    return "\n\n".join(compiled_laws)


def load_workspace_rules(workspace_root: Path) -> str:
    cline_rules = workspace_root / ".clinerules"
    log("INFO", f"Loading workspace rules from {cline_rules}")
    content = read_text_file(cline_rules)
    if content is None:
        return missing_block("Workspace rules", cline_rules)
    return content


def normalize_skills(skill_names: Sequence[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for skill in skill_names:
        normalized = skill.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
    return deduped


def load_skills(skill_names: Sequence[str], openclaw_root: Path) -> str:
    normalized_skills = normalize_skills(skill_names)
    if not normalized_skills:
        return ""

    log("INFO", f"Injecting requested skills: {normalized_skills}")
    compiled_skills: list[str] = []
    for skill in normalized_skills:
        skill_file = openclaw_root / "skills" / skill / "SKILL.md"
        content = read_text_file(skill_file)
        body = content if content is not None else missing_block("Skill file", skill_file)
        compiled_skills.append(f"--- SKILL: {skill.upper()} ---\n{body}")

    return "\n\n".join(compiled_skills)


def build_golden_prompt(
    target_file: Path,
    task_desc: str,
    skills: Sequence[str],
    workspace_root: Path,
    openclaw_root: Path,
) -> str:
    prompt = [
        "# [CRITICAL MISSION] AUTONOMOUS RESEARCH RIGGING (ARR) PROTOCOL",
        "You are an elite Autonomous Experimental Rigger powered by OpenAI Codex.",
        "Your mission is to modify the codebase strictly adhering to the immutable laws and skills provided below.",
        "",
        "=======================================================",
        "### 1. WORKSPACE IMMUTABLE LAWS (.clinerules)",
        "=======================================================",
        load_workspace_rules(workspace_root),
        "",
        "=======================================================",
        "### 2. GLOBAL SYSTEM CORE LAWS",
        "=======================================================",
        load_system_laws(workspace_root / "docs" / "system_core"),
    ]

    skills_block = load_skills(skills, openclaw_root)
    if skills_block:
        prompt.extend(
            [
                "",
                "=======================================================",
                "### 3. INJECTED OPERATIONAL SKILLS",
                "=======================================================",
                skills_block,
            ]
        )

    prompt.extend(
        [
            "",
            "=======================================================",
            "### 4. MANDATORY EXECUTION PROTOCOL",
            "=======================================================",
            "Rule A: You MUST write a brief `PLAN.md` explicitly stating how you will respect constraints (e.g., 32GB RAM limit, Batch Size maximizing).",
            "Rule B: You MUST write or update `smoke_test.py` and EXECUTE IT locally to verify shape and OOM logic.",
            "Rule C: Follow Git-SSoT rules. Commit your changes locally before concluding.",
            "Rule D: Use your coding tools to directly edit the Target File to accomplish the Objective. DO NOT wait for further instructions.",
            "",
            "=======================================================",
            "### 5. TARGET OBJECTIVE",
            "=======================================================",
            f"Target File: {target_file}",
            f"Objective: {task_desc}",
            "",
            "Execute this mission now.",
        ]
    )

    return "\n".join(prompt)


def execute_codex(prompt: str, target_dir: Path, interactive: bool) -> None:
    prompt_file = Path("/tmp/arr_codex_prompt.txt")
    prompt_file.write_text(prompt, encoding="utf-8")
    log("INFO", f"Golden Prompt written to {prompt_file}")

    codex_bin = shutil.which("codex")
    if codex_bin is None:
        raise DispatchError("Required command not found: codex")

    # [Native Headless Mode]
    # We now use the built-in `codex exec` which bypasses all TUI constraints.
    # We pass '-' as the prompt argument so codex reads the prompt from stdin.
    cmd = [
        codex_bin,
        "exec",
        "--dangerously-bypass-approvals-and-sandbox",
        "-C",
        str(target_dir),
        "--json",
        "--color",
        "never",
        "-o",
        "/tmp/arr_codex_final_msg.txt",
        "-",
    ]

    log_path = Path("/tmp/arr_codex_output.jsonl")
    log("INFO", f"Bootstrapping Codex exec. JSONL Events: {log_path}")

    try:
        with log_path.open("w", encoding="utf-8") as output_handle:
            with prompt_file.open("r", encoding="utf-8") as stdin_handle:
                completed = subprocess.run(
                    cmd,
                    stdin=stdin_handle,
                    stdout=output_handle,
                    stderr=subprocess.STDOUT,
                    check=False,
                )
        if completed.returncode != 0:
            raise DispatchError(
                f"Codex exited with status {completed.returncode}. Prompt saved at {prompt_file}."
            )
    except OSError as exc:
        raise DispatchError(f"Failed to launch Codex: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ARR Skill-Aware Codex Dispatcher")
    parser.add_argument(
        "--target",
        "-t",
        required=True,
        help="Target file or directory path to audit",
    )
    parser.add_argument(
        "--goal",
        "-g",
        required=True,
        help="Description of the experimental reinforcement objective",
    )
    parser.add_argument(
        "--skills",
        "-s",
        nargs="+",
        default=[],
        help="List of OpenClaw skills to inject (e.g., kaggle omni-fetch)",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run Codex interactively in foreground",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the assembled Golden Prompt to stdout and exit safely.",
    )
    return parser.parse_args()


def validate_target_path(raw_target: str) -> Path:
    target_path = Path(raw_target).expanduser()
    if not target_path.exists():
        raise DispatchError(f"Target path does not exist: {target_path.resolve(strict=False)}")
    if not target_path.is_file() and not target_path.is_dir():
        raise DispatchError(f"Target path is neither a file nor directory: {target_path}")
    return target_path.resolve()


def main() -> int:
    args = parse_args()

    openclaw_root = resolve_openclaw_root()
    workspace_root = resolve_workspace_root(openclaw_root)
    target_path = validate_target_path(args.target)
    working_dir = target_path.parent if target_path.is_file() else target_path

    golden_prompt = build_golden_prompt(
        target_file=target_path,
        task_desc=args.goal,
        skills=args.skills,
        workspace_root=workspace_root,
        openclaw_root=openclaw_root,
    )

    if args.dry_run:
        print(golden_prompt)
        return 0

    log("INFO", f"Payload assembled. Target: {target_path}")
    log("INFO", f"Skills requested: {len(normalize_skills(args.skills))}")
    execute_codex(golden_prompt, working_dir, args.interactive)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DispatchError as exc:
        log("FATAL", str(exc))
        raise SystemExit(1)
