import os
import sys
import zipfile
import json
import datetime
import subprocess
import shutil
from pathlib import Path

# Standard Exclusions for "Minimal Cold Storage"
DEFAULT_EXCLUSIONS = [
    '__pycache__', '.git', '.ipynb_checkpoints', 'wandb', 'node_modules',
    'build', 'dist', '.DS_Store'
]
EXTENSION_EXCLUSIONS = [
    '.npz', '.ckpt', '.log', '.o', '.so', '.a', '.pyc'
]
# File names to ALWAYS keep even if they match exclusion patterns
MANDATORY_INCLUSIONS = [
    'best_model.pt', 'results.json', 'guto_5seed.json', 'main.pdf', 'main_anonymous.pdf'
]

def get_git_revision_hash() -> str:
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode('ascii').strip()
    except:
        return "not_a_git_repo"

def create_metadata(project_name, source_path):
    metadata = {
        "project_name": project_name,
        "archive_timestamp": datetime.datetime.now().isoformat(),
        "source_path": str(source_path),
        "git_commit": get_git_revision_hash(),
        "conda_env": os.environ.get('CONDA_DEFAULT_ENV', 'base'),
        "user": os.environ.get('USER', 'unknown')
    }
    return metadata

def archive_project(project_path, output_zip):
    print(f"Archiving {project_path} to {output_zip}...", flush=True)
    project_path = Path(project_path).resolve()
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add metadata.json
        metadata = create_metadata(project_path.name, project_path)
        metadata_content = json.dumps(metadata, indent=2)
        zipf.writestr('archive_metadata.json', metadata_content)
        
        for root, dirs, files in os.walk(project_path):
            rel_path = Path(root).relative_to(project_path)
            
            # Prune directories
            dirs[:] = [d for d in dirs if d not in DEFAULT_EXCLUSIONS and not d.startswith('.')]
            
            for file in files:
                file_path = Path(root) / file
                file_rel = rel_path / file
                
                # Skip the output zip if it's being created in the same tree
                if file_path.resolve() == Path(output_zip).resolve():
                    continue
                
                # Application of exclusions
                skip = False
                if file.startswith('.'): skip = True
                if file.endswith(tuple(EXTENSION_EXCLUSIONS)) and file not in MANDATORY_INCLUSIONS:
                    skip = True
                
                # Special check for large .pt files
                if file.endswith('.pt') and file not in MANDATORY_INCLUSIONS:
                    try:
                        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                        if file_size_mb > 50: # Skip non-mandatory models > 50MB
                            skip = True
                    except OSError:
                        skip = True
                
                if not skip:
                    zipf.write(file_path, file_rel)

def sync_archive(local_zip, project_name):
    print(f"\n--- Synchronization Protocol ---", flush=True)
    
    # 1. GPU Cluster
    gpu_target_dir = f"/jhdx0003008/workspace/projects_core/{project_name}/archive/"
    print(f"[*] Syncing to GPU: {gpu_target_dir}", flush=True)
    try:
        subprocess.run(["ssh", "gpu", f"mkdir -p {gpu_target_dir}"], check=True, capture_output=True)
        subprocess.run(["scp", local_zip, f"gpu:{gpu_target_dir}"], check=True, capture_output=True)
        print(f"[OK] GPU Cluster synchronization successful.", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] GPU Sync failed: {e.stderr.decode().strip()}", flush=True)
    
    # 2. Server 03 (Cold Storage)
    server03_target_dir = f"/Users/roy-003/cold_storage/{project_name}/"
    print(f"[*] Syncing to Server 03: {server03_target_dir}", flush=True)
    try:
        subprocess.run(["ssh", "03", f"mkdir -p {server03_target_dir}"], check=True, capture_output=True)
        subprocess.run(["scp", local_zip, f"03:{server03_target_dir}"], check=True, capture_output=True)
        print(f"[OK] Server 03 synchronization successful.", flush=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Server 03 Sync failed: {e.stderr.decode().strip()}", flush=True)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        project_path = os.getcwd()
    else:
        project_path = sys.argv[1]
        
    project_name = Path(project_path).name
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Standard local archive path
    archive_dir = Path(project_path) / "archive"
    archive_dir.mkdir(exist_ok=True)
    
    output_filename = f"{project_name}_Submission_{timestamp}.zip"
    output_path = archive_dir / output_filename
    
    archive_project(project_path, output_path)
    print(f"\nSuccessfully archived to {output_path}", flush=True)
    
    sync_archive(str(output_path), project_name)
    print("\nArchival and Multinode Sync Complete.", flush=True)
