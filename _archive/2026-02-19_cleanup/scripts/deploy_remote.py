import asyncio
import os
import sys
import tarfile
import argparse

# Add src to path to import skills
sys.path.append(os.path.join(os.getcwd(), 'research_tools'))

try:
    from skills.ssh_executor import SSHExecutor
except ImportError:
    # Fallback or error if not found
    print("⚠️ SSHExecutor skill not found. Ensure running from project root.")
    sys.exit(1)

SETUP_SCRIPTS = {
    "medtime": """
        # Ensure Conda Env
        source /root/miniconda3/etc/profile.d/conda.sh
        if ! conda env list | grep -q "medtime"; then
            echo "Creating conda env 'medtime'..."
            conda create -n medtime python=3.10 -y
        fi
        conda activate medtime
        
        # Install Deps
        cd projects/medtime
        if [ -f repair_env.sh ]; then
            bash repair_env.sh
        else
            pip install lightning transformers peft accelerate wandb
        fi
    """,
    "cogd": """
        # Ensure Conda Env
        source /root/miniconda3/etc/profile.d/conda.sh
        if ! conda env list | grep -q "cogd"; then
            echo "Creating conda env 'cogd'..."
            conda create -n cogd python=3.10 -y
        fi
        conda activate cogd
        
        # Install Deps (SAM2, Diffusion)
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 || true
        pip install lightning transformers peft accelerate wandb matplotlib pandas scikit-learn
    """,
    "calam": """
        # Ensure Conda Env
        source /root/miniconda3/etc/profile.d/conda.sh
        if ! conda env list | grep -q "calam"; then
            echo "Creating conda env 'calam'..."
            conda create -n calam python=3.10 -y
        fi
        conda activate calam
        
        # Install Deps (LLM)
        pip install vllm>=0.4.0
        pip install transformers accelerate google-generativeai jailbreakbench
    """,
    "frenet": """
        # Ensure Conda Env
        source /root/miniconda3/etc/profile.d/conda.sh
        if ! conda env list | grep -q "frenet"; then
            echo "Creating conda env 'frenet'..."
            conda create -n frenet python=3.10 -y
        fi
        conda activate frenet
        
        # Install Deps (SAM2, Medical)
        pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
        pip install nibabel simpleitk monai
        # SAM2 installation (assuming it's in a standardized location or pip)
        pip install git+https://github.com/facebookresearch/sam2.git
    """
}

async def main():
    parser = argparse.ArgumentParser(description="Deploy Code to Remote Server")
    parser.add_argument("--project", type=str, default="medtime", help="Project to deploy (medtime, cogd, or all)")
    parser.add_argument("--host", type=str, default=None, help="Override remote host")
    parser.add_argument("--skip-setup", action="store_true", help="Skip remote setup script")
    parser.add_argument("--smoke", action="store_true", help="Run smoke test after deploy")
    parser.add_argument("--run", type=str, help="Command to run after deployment (e.g. 'python script.py')")
    parser.add_argument("--action", type=str, default="deploy", choices=["deploy", "sync_down"], help="Action to perform")
    args = parser.parse_args()

    # Load Secrets for Sync/Deploy
    import json
    with open("secrets.json", "r") as f:
        secrets = json.load(f)
    remote_conf = secrets.get("remote", {})
    host = args.host or remote_conf.get("host")
    port = remote_conf.get("port", 22)
    user = remote_conf.get("user", "root")
    
    remote_base = "/root/research_workspace"

    if args.action == "sync_down":
        print(f"🔄 Syncing deliverables from {user}@{host}:{remote_base}...")
        # Rsync Command construction
        # We want to pull: Code (*.py, *.sh), Papers (*.tex, *.pdf, *.bib), Docs (*.md), Configs (*.json, *.yaml)
        # We want to ignore: data/, models/, checkpoints/, heavy binaries
        
        exclude_list = [
            "data/", "wanbd/", "__pycache__/", "*.git/", ".DS_Store",
            "*.pt", "*.pth", "*.ckpt", "*.h5", "*.npy", "*.onnx",
            "*.tar.gz", "*.zip", "*.mp4", "*.avi" # Heavy media
        ]
        
        exclude_args = []
        for exc in exclude_list:
            exclude_args.extend(["--exclude", exc])
            
        # We start by syncing specific useful directories to avoid scanning entire /root
        # Actually /root/research_bot structure is flat enough.
        
        cmd = [
            "rsync", "-avz",
            "-e", f"ssh -p {port}",
            "--prune-empty-dirs",
        ] + exclude_args + [
            f"{user}@{host}:{remote_base}/",
            "./" # Sync to current directory (openclaw root)
        ]
        
        print(f"   Command: {' '.join(cmd)}")
        import subprocess
        try:
            subprocess.run(cmd, check=True)
            print("\n✅ Sync Down SUCCESS! (Papers, Code, and Configs updated)")
        except subprocess.CalledProcessError as e:
            print(f"\n❌ Sync Down FAILED: {e}")
        return

    # --- DEPLOY ACTION ---
    project = args.project
    executor = SSHExecutor()
    
    print(f"🚀 Deploying '{project}' to Remote Server...")

    local_tar = f"{project}_deploy.tar.gz"
    remote_tar = f"{remote_base}/{local_tar}"
    
    # 1. Create Local Bundle
    print("📦 Creating deployment bundle...")
    with tarfile.open(local_tar, "w:gz") as tar:
        # Add Common Components
        print("   Adding src...")
        if os.path.exists("src"):
            tar.add("src", arcname="src", filter=lambda x: None if '__pycache__' in x.name else x)
        
        print("   Adding scripts...")
        if os.path.exists("scripts"):
            tar.add("scripts", arcname="scripts", filter=lambda x: None if '__pycache__' in x.name else x)
        
        if os.path.exists("projects/__init__.py"):
             tar.add("projects/__init__.py", arcname="projects/__init__.py")

        # Add Project(s)
        projects_to_add = [project] if project != "all" else ["medtime", "cogd", "calam", "frenet"]
        
        for p in projects_to_add:
            p_path = f"projects/{p}"
            if not os.path.exists(p_path):
                # Optionally check if it's in a different location or just warn
                if os.path.exists(p_path):
                     pass 
                else: 
                     # Check if user meant a different folder, but for now just warn
                     print(f"⚠️ Warning: Project path {p_path} not found.")
                     continue
                
            print(f"   Adding {p_path}...")
            # Filter logic
            def filter_project(tarinfo):
                name = tarinfo.name
                if '__pycache__' in name: return None
                if '.git' in name: return None
                if '.DS_Store' in name: return None
                if 'lanes' in name and '/lanes' in name: return None # Exclude heavy output
                if 'outputs' in name and '/outputs' in name: return None
                return tarinfo

            tar.add(p_path, arcname=p_path, filter=filter_project)

    # 2. Upload Bundle
    print(f"📤 Uploading {local_tar}...")
    await executor.execute_command(f"mkdir -p {remote_base}")
    await executor.push_file(local_tar, remote_tar)

    # 3. Extract and Setup
    print("⚙️ Setting up remote environment...")
    
    # Determine setup logic
    custom_setup = ""
    if project in SETUP_SCRIPTS:
        custom_setup = SETUP_SCRIPTS[project]
    
    setup_script = f"""
    cd {remote_base}
    tar -xzf {local_tar}
    
    export PYTHONPATH=$PYTHONPATH:{remote_base}:{remote_base}/src
    
    {custom_setup if not args.skip_setup else ""}
    """
    
    # Add Smoke Test Logic
    if args.smoke:
        if project == "medtime":
            setup_script += f"\npython -m projects.medtime.main --task baseline_rule_cn --smoke"
        elif project == "cogd":
            setup_script += f"\npython -m projects.cogd.main --task E1_CoGD_Smoke --smoke"
        elif project == "calam":
            # Simple check
            setup_script += f"\npython -c 'import vllm; print(\"VLLM OK\")'"
    
    # 4. Optional Run Command
    if args.run:
        print(f"▶️ Execution: {args.run}")
        # Execute in background or foreground? Foreground to see output.
        setup_script += f"\necho '--- RUN OUTPUT ---'\n{args.run}"

    result = await executor.execute_command(setup_script)
    
    print("\n=== REMOTE OUTPUT ===\n")
    print(result.get("stdout", ""))
    if result.get("stderr"):
        print("--- STDERR ---")
        print(result.get("stderr"))
        
    if result.get("exit_code") == 0:
        print("\n✅ Deployment SUCCESS!")
    else:
        print("\n❌ Deployment FAILED.")
        
    # Cleanup local tar
    if os.path.exists(local_tar):
        os.remove(local_tar)

if __name__ == "__main__":
    asyncio.run(main())
