#!/usr/bin/env python3
import argparse
import os
from dotenv import load_dotenv
import paramiko
from scp import SCPClient

load_dotenv()

def resilient_connect(client, port, user, pkey, pwd, max_retries=3):
    # Single Primary Jump Path Resilience Logic
    primary_host = os.environ.get("SSH_HOST")
    
    for attempt in range(1, max_retries + 1):
        try:
            client.connect(primary_host, port=port, username=user, pkey=pkey, password=pwd, timeout=8)
            return True
        except Exception as e:
            print(f"⚠️ [Attempt {attempt}/{max_retries}] Tunnel to [{primary_host}] shuddered: {e}")
            if attempt < max_retries:
                import time
                time.sleep(3)  # Cooldown before reconnection
            else:
                print(f"❌ Critical failure: Cannot penetrate [{primary_host}] after {max_retries} attempts.")
                return False
def fallback_connect(client, port, user, pkey, pwd):
    # HA ProxyJump Fallback Logic
    primary_host = os.environ.get("SSH_HOST")
    backup_host = os.environ.get("SSH_BACKUP_HOST") # Node 03 Fallback
    
    # Try primary
    try:
        # print(f"HA Router: Dialing Primary 🚀 [{primary_host}]")
        client.connect(primary_host, port=port, username=user, pkey=pkey, password=pwd, timeout=5)
        return True
    except Exception as e:
        print(f"⚠️ Primary tunnel [{primary_host}] collapsed: {e}")
        if backup_host:
            print(f"🔄 Activating Fallback Router (Apollo Protocol) ➔ [{backup_host}]")
            try:
                client.connect(backup_host, port=port, username=user, pkey=pkey, password=pwd, timeout=8)
                print("✅ Fallback tunnel established!")
                return True
            except Exception as backup_e:
                print(f"❌ Fallback tunnel also failed: {backup_e}")
                return False
        return False

from typing import Optional

def get_client(host: Optional[str] = None, user: Optional[str] = None, port: Optional[int] = None, key_path: Optional[str] = None, password: Optional[str] = None) -> Optional[paramiko.SSHClient]:
    host = host or os.environ.get("SSH_HOST")
    user = user or os.environ.get("SSH_USER")
    key_path = key_path or os.environ.get("SSH_KEY")
    password = password or os.environ.get("SSH_PASS")
    port = port if port is not None else int(os.environ.get("SSH_PORT", 22))
    
    # print(f"DEBUG: User={user} Host={host} Key={key_path} PassLen={len(password) if password else 0}")
    
    if not host or not user:
        raise ValueError("SSH_HOST and SSH_USER must be set in .env")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # Load SSH Config for ProxyCommand (e.g., Jump Host)
    sock = None
    try:
        conf = paramiko.SSHConfig()
        conf_path = os.path.expanduser("~/.ssh/config")
        if os.path.exists(conf_path):
            with open(conf_path) as f:
                conf.parse(f)
        hconf = conf.lookup(host)
        if 'proxycommand' in hconf:
            sock = paramiko.ProxyCommand(hconf['proxycommand'])
        if 'hostname' in hconf:
            host = hconf['hostname']
        if 'user' in hconf and not os.environ.get("SSH_USER"):
            user = hconf['user']
        if 'identityfile' in hconf and not key_path:
            key_path = os.path.expanduser(hconf['identityfile'][0])
        
        # If the host was found in config, prioritize its port or fallback to 22 (ignoring environment ghosts)
        if 'port' in hconf:
            port = int(hconf['port'])
        else:
            port = 22
    except Exception as e:
        print(f"DEBUG: ProxyCommand parse failed: {e}")

    # helper to try connection
    def try_connect(pkey=None, pwd=None):
        try:
            client.connect(host, port=port, username=user, pkey=pkey, password=pwd, timeout=15, sock=sock)
            return True
        except paramiko.AuthenticationException:
            # print(f"Auth Failed (pkey={bool(pkey)}, pwd={bool(pwd)}): {e}")
            return False
        except Exception as e:
            print(f"Connection Error: {e}")
            return False

    # 1. Try Key (if exists)
    if key_path:
        k = None
        # Load Key Logic
        if "-----BEGIN" in key_path:
             import io
             f = io.StringIO(key_path)
             try: k = paramiko.Ed25519Key.from_private_key(f)
             except: 
                 f.seek(0)
                 k = paramiko.RSAKey.from_private_key(f)
        elif os.path.isfile(key_path):
             # Helper to load key
             def load_key(path, cls, pwd=None):
                 try: return cls.from_private_key_file(path, password=pwd)
                 except: return None

             # Try Ed25519 then RSA, with and without password
             k = load_key(key_path, paramiko.Ed25519Key)
             if not k: k = load_key(key_path, paramiko.RSAKey)
             if not k and password:
                 print("Attempting to decrypt key with SSH_PASS...")
                 k = load_key(key_path, paramiko.Ed25519Key, password)
                 if not k: k = load_key(key_path, paramiko.RSAKey, password)
        
        if k:
            if try_connect(pkey=k): return client
            print("Key authentication failed. Trying password...")

    # 2. Try Password
    if password:
        if try_connect(pwd=password): return client
        
    # 3. Try Default Agent / Default Keys (If no explicit method was presented or previous auth failed)
    print("Trying default SSH-Agent or default keys...")
    if try_connect(pkey=None, pwd=None): return client
    
    print("All authentication methods failed.")
    return None

def get_env_prefix():
    # Gather env vars to inject
    is_windows = os.environ.get("SSH_IS_WINDOWS", "0") == "1"
    keys = ["WANDB_API_KEY", "HF_TOKEN"]
    exports = []
    
    if is_windows:
        return "" # Disable env injection for Windows explicitly

    for k in keys:
        v = os.environ.get(k)
        if v:
            exports.append(f"export {k}='{v}'")
    
    if not exports: return ""
    return " ".join(exports) + ";"

# Default Conda Path (Update based on server config)
CONDA_BIN = "/root/miniconda3/bin/conda"

def get_conda_prefix(env_name):
    if not env_name: return ""
    return f"{CONDA_BIN} run -n {env_name} --no-capture-output "

def exec_command(args):
    client = get_client()
    if not client: return

    cmd = args.command
    detach = args.detach
    conda_env = args.conda_env
    
    env_prefix = get_env_prefix()
    
    # If conda_env is set, wrap the command
    real_cmd = cmd
    if conda_env:
        real_cmd = f"{CONDA_BIN} run -n {conda_env} --no-capture-output {cmd}"
        
    full_cmd = f"{env_prefix} {real_cmd}"
    
    if detach:
        # Run offline with nohup
        print(f"Executing (Detached): {cmd}")
        # nohup cmd > nohup.out 2>&1 & echo $!
        nohup_cmd = f"nohup sh -c '{full_cmd}' > nohup.out 2>&1 & echo $!"
        stdin, stdout, stderr = client.exec_command(nohup_cmd)
        pid = stdout.read().decode('utf-8', errors='replace').strip()
        print(f"Started in background. PID: {pid}")
    else:
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = client.exec_command(full_cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if out: print(out)
        if err: print(f"Stderr: {err}")
    
    client.close()
    
    client.close()

def upload_file(args):
    client = get_client()
    if not client: return
    
    sftp = client.open_sftp()
    local = args.local
    remote = args.remote
    resume = args.resume
    
    if os.path.isdir(local):
        print(f"Uploading directory {local} -> {remote}")
        with SCPClient(client.get_transport()) as scp:
            scp.put(local, remote, recursive=True)
        print("Directory upload complete.")
        return

    if resume:
        try:
            r_stat = sftp.stat(remote)
            l_size = os.path.getsize(local)
            if r_stat.st_size == l_size:
                print(f"Skipping {local} (Remote size matches)")
                return
            else:
                 print(f"Resuming/Overwriting {local} (Size mismatch)")
        except FileNotFoundError:
            pass 
        except Exception:
            pass 

    print(f"Uploading {local} -> {remote}")
    sftp.put(local, remote)
    print("Upload complete.")
    sftp.close()
    client.close()

    client.close()

def write_file(args):
    client = get_client()
    if not client: return
    
    sftp = client.open_sftp()
    remote = args.remote
    content = args.content
    
    print(f"Writing to {remote}...")
    with sftp.open(remote, "w") as f:
        f.write(content)
    
    print("Write complete.")
    sftp.close()
    client.close()

def download_file(args):
    client = get_client()
    if not client: return
    
    print(f"Downloading {args.remote} -> {args.local}")
    with SCPClient(client.get_transport()) as scp:
        scp.get(args.remote, args.local)
        
    client.close()
    print("Download complete.")

def run_project(args):
    client = get_client()
    if not client: return
    
    local_dir = args.local_dir
    entry_point = args.entry_script
    detach = args.detach
    remote_work_dir = "/tmp/openclaw_work"
    
    import shutil
    import tempfile
    
    print(f"Zipping {local_dir}...")
    base = os.path.basename(os.path.abspath(local_dir))
    zip_name = f"{base}.zip"
    
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = shutil.make_archive(os.path.join(tmpdir, base), 'zip', local_dir)
        
        remote_zip = f"{remote_work_dir}/{zip_name}"
        print(f"Uploading to {remote_zip}...")
        client.exec_command(f"mkdir -p {remote_work_dir}")
        
        with SCPClient(client.get_transport()) as scp:
            scp.put(zip_path, remote_zip)
            
        remote_project_dir = f"{remote_work_dir}/{base}"
        setup_cmd = f"unzip -o {remote_zip} -d {remote_project_dir}"
        
        setup_cmd = f"unzip -o {remote_zip} -d {remote_project_dir}"
        
        env_prefix = get_env_prefix()
        
        # Prepare python command
        py_cmd = f"python {entry_point}"
        if args.conda_env:
             py_cmd = f"{CONDA_BIN} run -n {args.conda_env} --no-capture-output python {entry_point}"
             
        run_cmd = f"cd {remote_project_dir} && {env_prefix} {py_cmd}"
        
        if detach:
            log_file = f"{remote_work_dir}/{base}.log"
            full_cmd = f"nohup sh -c '{setup_cmd} && {run_cmd}' > {log_file} 2>&1 & echo $!"
            stdin, stdout, stderr = client.exec_command(full_cmd)
            pid = stdout.read().decode().strip()
            print(f"Project running in background. PID: {pid}")
            print(f"Logs will be at: {log_file}")
            print(f"Use: ssh_tool.py exec 'cat {log_file}' to view.")
        else:
            full_cmd = f"{setup_cmd} && {run_cmd}"
            stdin, stdout, stderr = client.exec_command(full_cmd)
            print("--- REMOTE OUTPUT ---")
            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                    print(stdout.channel.recv(1024).decode(), end="")
            print(stdout.read().decode(), end="")
            err = stderr.read().decode()
            if err: print(f"\nSTDERR: {err}")
            print("\n---------------------")
        
    client.close()

def gpu_status(args):
    client = get_client()
    if not client: return
    
    print("Checking GPU Status...")
    stdin, stdout, stderr = client.exec_command("nvidia-smi")
    out = stdout.read().decode().strip()
    if out:
        print(out)
    else:
        err = stderr.read().decode().strip()
        print(f"Failed to get GPU status: {err}")
    
    client.close()

def conda_manager(args):
    client = get_client()
    if not client: return

    sub = args.subcommand
    name = args.name
    packages = " ".join(args.packages) if args.packages else ""
    
    cmd = ""
    if sub == "create":
        if not packages: packages = "python=3.9" # default
        cmd = f"{CONDA_BIN} create -y -n {name} {packages}"
    elif sub == "clone":
        if not args.clone_from:
            print("Error: --clone-from required for clone")
            return
        cmd = f"{CONDA_BIN} create -y -n {name} --clone {args.clone_from}"
    elif sub == "delete":
        cmd = f"{CONDA_BIN} env remove -y -n {name}"
    elif sub == "install":
        if not packages: 
             print("Error: packages required for install")
             return
        cmd = f"{CONDA_BIN} install -y -n {name} {packages}"
    elif sub == "update":
        if not packages:
             # update all
             cmd = f"{CONDA_BIN} update -y -n {name} --all"
        else:
             cmd = f"{CONDA_BIN} update -y -n {name} {packages}"
    elif sub == "list":
        cmd = f"{CONDA_BIN} env list"
    elif sub == "install-manager":
        # Check if exists
        check_cmd = f"ls {CONDA_BIN}"
        stdin, stdout, stderr = client.exec_command(check_cmd)
        if stdout.channel.recv_exit_status() == 0:
            print("Conda already installed.")
            client.close()
            return

        print("Installing Miniconda...")
        # Download
        installer = "Miniconda3-latest-Linux-x86_64.sh"
        dl_cmd = f"wget https://repo.anaconda.com/miniconda/{installer} -O /tmp/{installer}"
        stdin, stdout, stderr = client.exec_command(dl_cmd)
        print(stdout.read().decode())
        
        # Install
        print("Running installer...")
        install_cmd = f"bash /tmp/{installer} -b -p /root/miniconda3"
        stdin, stdout, stderr = client.exec_command(install_cmd)
        out = stdout.read().decode().strip()
        print(out)
        
        # Init?
        # client.exec_command(f"{CONDA_BIN} init bash")
        print("Conda installed to /root/miniconda3")
        client.close()
        return

    if cmd:
        if args.detach:
            print(f"Executing Conda (Detached): {cmd}")
            # Use specific log file for conda ops to avoid overwriting general nohup.out if possible
            # or just use nohup.out. Let's use a timestamped or named log? 
            # Simple for now: conda_{name}.log
            log_file = f"conda_{name if name else 'op'}.log"
            nohup_cmd = f"nohup sh -c '{cmd}' > {log_file} 2>&1 & echo $!"
            stdin, stdout, stderr = client.exec_command(nohup_cmd)
            pid = stdout.read().decode().strip()
            print(f"Started in background. PID: {pid}")
            print(f"Logs will be written to: {log_file}")
        else:
            print(f"Executing Conda: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            
            # Stream output
            while not stdout.channel.exit_status_ready():
                if stdout.channel.recv_ready():
                   print(stdout.channel.recv(1024).decode(), end="")
            
            print(stdout.read().decode(), end="")
    client.close()

def main():
    import sys
    import os
    argv, new_argv, i = sys.argv[1:], [], 0
    while i < len(argv):
        arg = argv[i]
        if arg in ('--host', '-H'):
            i += 1
            if i < len(argv): os.environ['SSH_HOST'] = argv[i]
        elif arg.startswith('--host='):
            os.environ['SSH_HOST'] = arg.split('=', 1)[1]
        elif arg in ('--user', '-U'):
            i += 1
            if i < len(argv): os.environ['SSH_USER'] = argv[i]
        elif arg.startswith('--user='):
            os.environ['SSH_USER'] = arg.split('=', 1)[1]
        else:
            new_argv.append(arg)
        i += 1
    sys.argv = [sys.argv[0]] + new_argv

    parser = argparse.ArgumentParser(description="OpenClaw SSH Tool")
    parser.add_argument("--host", "-H", help="Target SSH host (can be placed anywhere)", default=argparse.SUPPRESS)
    parser.add_argument("--user", "-U", help="Target SSH user (can be placed anywhere)", default=argparse.SUPPRESS)
    subparsers = parser.add_subparsers(dest="action")
    
    e_parser = subparsers.add_parser("exec")
    e_parser.add_argument("command", help="Command to execute")
    e_parser.add_argument("--detach", action="store_true", help="Run in background (offline)") # NEW
    e_parser.add_argument("--conda_env", help="Run in specific Conda environment") # NEW
    
    u_parser = subparsers.add_parser("upload")
    u_parser.add_argument("local", help="Local path")
    u_parser.add_argument("remote", help="Remote path")
    u_parser.add_argument("--resume", action="store_true", help="Skip if file exists and size matches")
    
    w_parser = subparsers.add_parser("write")
    w_parser.add_argument("remote", help="Remote path")
    w_parser.add_argument("content", help="Content to write")
    
    d_parser = subparsers.add_parser("download")
    d_parser.add_argument("remote", help="Remote path")
    d_parser.add_argument("local", help="Local path")

    p_parser = subparsers.add_parser("run_project")
    p_parser.add_argument("local_dir", help="Local project directory")
    p_parser.add_argument("entry_script", help="Relative path to entry script")
    p_parser.add_argument("--detach", action="store_true", help="Run in background (offline)") # NEW
    p_parser.add_argument("--conda_env", help="Run in specific Conda environment") # NEW

    # GPU Status
    g_parser = subparsers.add_parser("gpu_status")

    # Conda
    c_parser = subparsers.add_parser("conda")
    c_parser.add_argument("subcommand", choices=["create", "clone", "delete", "install", "update", "list", "install-manager"])
    c_parser.add_argument("-n", "--name", help="Environment name")
    c_parser.add_argument("--clone-from", help="Source env for clone")
    c_parser.add_argument("--packages", nargs="*", help="Packages to install/create with")
    c_parser.add_argument("--detach", action="store_true", help="Run in background")
    
    args = parser.parse_args()
# ... rest same
    
    if args.action == "exec":
        exec_command(args)
    elif args.action == "upload":
        upload_file(args)
    elif args.action == "write":
        write_file(args)
    elif args.action == "download":
        download_file(args)
    elif args.action == "run_project":
        run_project(args)
    elif args.action == "gpu_status":
        gpu_status(args)
    elif args.action == "conda":
        conda_manager(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
