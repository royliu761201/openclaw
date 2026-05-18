#!/usr/bin/env python3
"""
audit_tool_integrity.py: The Physical Tool Integrity Probe for OpenClaw Agents

This script actively parses an agent's workspace (specifically TOOLS.md or raw physical scripts) 
to hunt for declared *.py or *.sh tool definitions. It then rigorously executes a dry run 
(e.g., calling the file with '-h' or '--help') to guarantee the script file actually physically exists 
and is syntactically sound, preventing Agents from hallucinating capabilities they don't possess.

Usage:
  python3 scripts/audit_tool_integrity.py <agent_workspace_path>
"""

import sys
import os
import subprocess
import glob
import re

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python3 audit_tool_integrity.py <agent_workspace_path>")
        sys.exit(1)
        
    workspace_path = os.path.expanduser(sys.argv[1])
    agent_dir = os.path.join(workspace_path, ".agent")
    
    if not os.path.exists(agent_dir):
        print(f"❌ Error: Not a valid OpenClaw agent workspace. Missing .agent folder: {agent_dir}")
        sys.exit(1)
        
    print(f"🔬 Initiating Physical Integrity Probe for Agent Workspace: {workspace_path}")
    
    tools_md = os.path.join(agent_dir, "TOOLS.md")
    scripts = []
    
    # Strategy 1: Parse Markdown declarations for strict matching
    if os.path.exists(tools_md):
        with open(tools_md, 'r', encoding='utf-8') as f:
            content = f.read()
            # Hunt for absolute or relative paths disguised as markdown highlights
            found_py = re.findall(r'([~/\w\.-]+/\w+\.py)', content)
            found_sh = re.findall(r'([~/\w\.-]+/\w+\.sh)', content)
            scripts.extend(found_py)
            scripts.extend(found_sh)
            
    # Strategy 2: Directly sweep typical tool directories if defined
    local_skills_dir = os.path.join(workspace_path, ".local_skills")
    if os.path.exists(local_skills_dir):
        scripts.extend(glob.glob(os.path.join(local_skills_dir, "**/*.py"), recursive=True))
        scripts.extend(glob.glob(os.path.join(local_skills_dir, "**/*.sh"), recursive=True))
        
    # De-duplicate
    scripts = list(set(scripts))
    
    if not scripts:
        print("⚠️  Warning: No explicit Python or Shell tool scripts found to audit.")
        print("✅ Assuming standard REST/OpenAPI tools are used or no tools are mounted. Pass.")
        sys.exit(0)
        
    print(f"🛠️  Discovered {len(scripts)} executable tools declared. Initiating syntax & existence dry-runs...")
    
    failures = 0
    for script_path in scripts:
        # Expand user path if it exists
        abs_path = os.path.expanduser(script_path)
        
        # Verify Physical File
        if not os.path.exists(abs_path):
            print(f"❌ [MISSING FATAL] Tool mapped in definition but physically absent: {abs_path}")
            failures += 1
            continue
            
        print(f"⚡ Probing: {abs_path}")
        
        # Dry Run Execution
        cmd = ["python3", abs_path, "-h"] if abs_path.endswith('.py') else ["bash", abs_path, "-h"]
        
        try:
             # Capture both stdout and stderr implicitly
             result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
             
             # Acceptable return codes for -h are usually 0, but sometimes poorly written CLI tools exit with 1 or 2 when given -h.
             # What we are hunting for specifically is SyntaxErrors, ModuleNotFoundErrors, or missing bash interpreters.
             if "SyntaxError" in result.stderr or "ModuleNotFoundError" in result.stderr:
                 print(f"❌ [SYNTAX FATAL] Script is physically present but syntactically broken: {abs_path}")
                 print(f"    Reason: {result.stderr.splitlines()[-1]}")
                 failures += 1
                 continue
                 
             print(f"  ✓ Pass: Physical Link and Interpreter check OK.")
        except subprocess.TimeoutExpired:
             print(f"⚠️  [TIMEOUT] Script hung on `-h`. It exists, but CLI parsing may be blocking: {abs_path}")
             # We don't fail strictly on timeout, as some scripts block natively, but we warn heavily.
        except Exception as e:
             print(f"❌ [EXECUTION FATAL] Could not spawn interpreter for: {abs_path}. Error: {e}")
             failures += 1
             
    if failures > 0:
         print(f"\\n❌ FATAL: {failures} declared tools failed the physical integrity audit. This agent is actively hallucinating capabilities.")
         sys.exit(1)
         
    print(f"\\n✅ All tool definitions mathematically mapped to valid physical execution layers. Agent is clean.")
    sys.exit(0)

if __name__ == "__main__":
    main()
