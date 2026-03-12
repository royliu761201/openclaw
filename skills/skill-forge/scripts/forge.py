import os
import sys
import argparse
import subprocess
import shutil

# ---------------------------------------------------------------------------
# SSoT Constants (System Truths)
# ---------------------------------------------------------------------------
OPENCLAW_ROOT = os.path.expanduser("~/openclaw")
SKILLS_DIR = os.path.join(OPENCLAW_ROOT, "skills")
WHEELS_CACHE_DIR = "/tmp/wheels_cache"
NODE_03_VAULT = "03:~/openclaw_data/wheels_vault/"

def create_scaffold(skill_name):
    """Phase 1: Zero-Day Scaffold. Creates the directory, lock files, and templates."""
    print(f"[{skill_name}] Initiating Zero-Day Scaffold...")
    target_dir = os.path.join(SKILLS_DIR, skill_name)
    scripts_dir = os.path.join(target_dir, "scripts")
    
    if os.path.exists(target_dir):
        print(f"❌ Abort: Skill '{skill_name}' already exists at {target_dir}")
        sys.exit(1)
        
    os.makedirs(scripts_dir)
    print(f"✅ Created directory structure: {target_dir}")
    
    # 1. The Gitignor Shield
    gitignore_path = os.path.join(target_dir, ".gitignore")
    with open(gitignore_path, "w") as f:
        f.write("venv/\n__pycache__/\n*.whl\n*.pt\n*.onnx\n*.safetensors\n*.bin\nmodels/\nopenclaw_data_links/\n")
    print(f"✅ Forged Anti-Pollution Shield: {gitignore_path}")
    
    # 2. Requirements template
    req_path = os.path.join(target_dir, "requirements_core.txt")
    with open(req_path, "w") as f:
        f.write("# Enter core heavy dependencies here, e.g., onnxruntime, torch, etc.\n")
        f.write("# DO NOT run pip install. Use `python3 forge.py --harvest <skill_name>`\n")
        
    # 3. The L1 Jailbroken Python Template
    py_template_path = os.path.join(scripts_dir, f"{skill_name.replace('-', '_')}_tool.py")
    with open(py_template_path, "w") as f:
        f.write('"""\n')
        f.write(f'Auto-Generated Entrypoint for {skill_name}\n')
        f.write('Enforces Sandbox Incarceration Law (L1 Constitution Rule 12)\n')
        f.write('"""\n')
        f.write('import sys\nimport os\n\n')
        f.write('# --- L1 SANDBOX INCARCERATION PROBE ---\n')
        f.write('in_venv = sys.prefix != sys.base_prefix\n')
        f.write('if not in_venv:\n')
        f.write('    print("⚠️ [L1 PROBE] Global scope detected. Self-incarcerating into VENV...")\n')
        f.write('    venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "venv/bin/python3")\n')
        f.write('    if not os.path.exists(venv_python):\n')
        f.write('        print("❌ Fatal: Sandbox VENV not found. Run Hermetic Drop deploy script first.")\n')
        f.write('        sys.exit(1)\n')
        f.write('    os.execv(venv_python, [venv_python] + sys.argv)\n')
        f.write('# ------------------------------------------\n\n')
        f.write('def main():\n')
        f.write(f'    print("[{skill_name}] Running securely inside VENV.")\n\n')
        f.write('if __name__ == "__main__":\n')
        f.write('    main()\n')
        
    os.chmod(py_template_path, 0o755)
    print(f"✅ Generated secure sandbox entrypoint: {py_template_path}")
    
    # 4. Installation Script Template
    sh_template_path = os.path.join(target_dir, "install_isolation.sh")
    with open(sh_template_path, "w") as f:
        f.write("#!/bin/bash\n")
        f.write('set -e\n')
        f.write('echo "🛡️ Initiating Hermetic Drop Installation..."\n')
        f.write('DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"\n')
        f.write('cd "$DIR"\n\n')
        f.write('echo "1/3 Destroying old world..."\n')
        f.write('rm -rf venv # clear existing sandbox cache\n')
        f.write('python3 -m venv venv\n\n')
        f.write('echo "2/3 Engaging Sandbox Vacuum (No-Network Policy Limit)..."\n')
        f.write('# IMPORTANT: Change RAW_DATA_DIR to point to your physical WHEELS_CACHE_DIR on the target node.\n')
        f.write('RAW_DATA_DIR="/tmp/wheels_cache/' + skill_name + '"\n')
        f.write('if [ ! -d "$RAW_DATA_DIR" ]; then\n')
        f.write('    echo "❌ Missing RAW Data. Did you sync the wheels from Vault?"\n')
        f.write('    exit 1\n')
        f.write('fi\n\n')
        f.write('echo "3/3 Blind Injection (__NO__ Http Traffic allowed)..."\n')
        f.write('./venv/bin/pip install --no-index --find-links="$RAW_DATA_DIR" --no-deps "$RAW_DATA_DIR"/*.whl\n')
        f.write('echo "✅ Hermetic Drop Complete."\n')
        
    os.chmod(sh_template_path, 0o755)
    print(f"✅ Generated Isolation Installer: {sh_template_path}")
    print(f"\n🚀 Phase 1 Done. Next: Edit {req_path} and run '--harvest'.")

def harvest_wheels(skill_name):
    """Phase 2: Hermetic Harvester. Downloads wheels without installing."""
    print(f"[{skill_name}] Engaging Hermetic Vacuum...")
    target_dir = os.path.join(SKILLS_DIR, skill_name)
    req_path = os.path.join(target_dir, "requirements_core.txt")
    
    if not os.path.exists(req_path):
         print(f"❌ Abort: {req_path} not found. Run --init first.")
         sys.exit(1)
         
    skill_wheel_dir = os.path.join(WHEELS_CACHE_DIR, skill_name)
    os.makedirs(skill_wheel_dir, exist_ok=True)
    
    print(f"📥 Pulling dependencies into physical box: {skill_wheel_dir}")
    # Run pip download
    cmd = [
        sys.executable, "-m", "pip", "download", 
        "-r", req_path, 
        "-d", skill_wheel_dir,
        "-i", "https://pypi.doubanio.com/simple/"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Vacuum successful. {len(os.listdir(skill_wheel_dir))} packages trapped in {skill_wheel_dir}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Vacuum failed. Ensure Node 01 network/proxy is healthy.")
        sys.exit(1)
        
    print(f"\n📦 Preparing Orbital Drop Payload for Vault 03...")
    zip_target = os.path.join(WHEELS_CACHE_DIR, f"{skill_name}_wheels.zip")
    shutil.make_archive(zip_target.replace('.zip',''), 'zip', skill_wheel_dir)
    print(f"✅ Payload forged: {zip_target}")
    
    print(f"🚀 Escorting Payload to Vault 03 ({NODE_03_VAULT})...")
    scp_cmd = ["scp", zip_target, NODE_03_VAULT]
    try:
         subprocess.run(scp_cmd, check=True)
         print(f"✅ Payload secured in Vault 03. Total SSoT isolation achieved.")
    except Exception as e:
         print(f"⚠️ SCP failed. Please manually sync {zip_target} to the Vault.")

def deploy_payload(skill_name, target_node):
    """Phase 3: Orbital Drop. Synchronizes scripts and instructs the remote node."""
    print(f"[{skill_name}] Initiating Orbital Drop to Node {target_node}...")
    print("⏳ This phase requires the master ssh-tool integration (AB-012/AB-022 strict compliance).")
    print("For now, use git push/pull to sync the scripts, and scp the payload from Vault.")
    print(f"1. On {target_node}: git pull origin mac")
    print(f"2. On {target_node}: scp 03:~/openclaw_data/wheels_vault/{skill_name}_wheels.zip /tmp/")
    print(f"3. On {target_node}: unzip /tmp/{skill_name}_wheels.zip -d /tmp/wheels_cache/{skill_name}")
    print(f"4. On {target_node}: bash ~/openclaw/skills/{skill_name}/install_isolation.sh")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skill Forge - The Local AI Factory")
    parser.add_argument("--init", type=str, metavar="SKILL_NAME", help="Generate zero-day scaffold")
    parser.add_argument("--harvest", type=str, metavar="SKILL_NAME", help="Vacuum dependencies to physical storage")
    parser.add_argument("--deploy", nargs=2, metavar=("SKILL_NAME", "TARGET_NODE"), help="Initiate orbital drop")
    
    args = parser.parse_args()
    
    if args.init:
        create_scaffold(args.init)
    elif args.harvest:
        harvest_wheels(args.harvest)
    elif args.deploy:
        deploy_payload(args.deploy[0], args.deploy[1])
    else:
        parser.print_help()
