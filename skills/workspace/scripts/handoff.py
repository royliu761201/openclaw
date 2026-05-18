#!/usr/bin/env python3
import os
import sys
import subprocess
import datetime
from pathlib import Path

def get_brain_context():
    # Priority 1: Use direct OS variable
    brain_dir = os.environ.get('BRAIN_DIR', '')
    if not brain_dir:
        # Priority 2: Scan for most recent brain in local appdata path
        home = str(Path.home())
        brain_root = Path(home) / ".gemini" / "antigravity" / "brain"
        if brain_root.exists():
            brains = sorted([x for x in brain_root.iterdir() if x.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)
            if brains:
                brain_dir = str(brains[0])
    
    if not brain_dir:
        return "No brain context found."
    
    brain_path = Path(brain_dir)
    context = []
    
    # Task Progress Summary
    task_file = brain_path / "task.md"
    if task_file.exists():
        try:
            lines = task_file.read_text().splitlines()
            done = [l for l in lines if "[x]" in l]
            pending = [l for l in lines if "[ ]" in l or "[/]" in l]
            context.append(f"Tasks: {len(done)} Done / {len(pending)} Remaining")
            if pending:
                context.append("Pending: " + " | ".join([p.strip("- [ ]").strip() for p in pending[:2]]))
        except:
            pass

    # Active Design Snapshot
    impl_plan = brain_path / "implementation_plan.md"
    if impl_plan.exists():
        context.append(f"Active Design: {impl_plan.name}")

    return " | ".join(context) if context else "Found brain, but no specific tasks yet."

def get_process_context():
    try:
        # Scan for active research processes (SSH, Rsync, Python runs)
        cmd = ["ps", "-eo", "pid,start,command"]
        output = subprocess.check_output(cmd).decode('utf-8').splitlines()
        
        keywords = ["rsync", "ssh", "python3", "bench", "train", "cold_archiver"]
        active = []
        for line in output:
            if any(k in line for k in keywords) and "grep" not in line and "handoff.py" not in line:
                active.append(line.strip())
        
        if active:
            return " | ".join(active[:5])
        return "None active."
    except:
        return "Process scan failed."

def generate_super_prompt():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    brain_ctx = get_brain_context()
    proc_ctx = get_process_context()
    
    # Format strings outside the f-string to satisfy Python 3.9 backslash rules
    clean_brain = brain_ctx.replace('\n', ' ')
    clean_proc = proc_ctx.replace('\n', ' ')
    
    prompt = f"""# 🚀 SESSION CONTINUITY HANDOFF ({timestamp})

## 🧠 Brain Context
{brain_ctx}

## 🖥️ System Context
{proc_ctx}

## 🏁 Super-Prompt (Paste into NEW Session)
> **[SSoT Continuity]** Resuming NeurIPS Research Sprint. {timestamp}.
> 
> **Status**: [L1 现场] {clean_brain}
> **Active Hardware**: [L0 尸检] {clean_proc}
> **Next Objective**: Prepare to monitor existing benchmarks and execute the pending tasks.
"""
    return prompt

if __name__ == "__main__":
    print(generate_super_prompt())
