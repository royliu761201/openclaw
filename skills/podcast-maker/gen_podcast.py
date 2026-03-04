import os
import sys
import json
import argparse
import paramiko
import time
import requests
from dotenv import load_dotenv

def get_env_var(var_name):
    # Try OS environ first, then fallback to .env file parsing manually
    if var_name in os.environ:
        return os.environ[var_name]
        
    env_path = "/Users/roy-jd/Documents/projects/openclaw/.env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith(f"{var_name}="):
                    # Strip quotes and newline
                    return line.strip().split("=", 1)[1].strip("'\"")
    return None

def main():
    parser = argparse.ArgumentParser(description="Generate a podcast audio file using a remote GPU ChatTTS server.")
    parser.add_argument("--input", required=True, help="Path to the JSON script file.")
    parser.add_argument("--output", required=True, help="Path to save the generated output .ogg file.")
    args = parser.parse_args()

    # Load credentials
    host = get_env_var('SSH_HOST')
    port = int(get_env_var('SSH_PORT') or 22)
    user = get_env_var('SSH_USER')
    password = get_env_var('SSH_PASS')
    
    if not all([host, user, password]):
        print("Error: Missing SSH credentials in .env", file=sys.stderr)
        sys.exit(1)
        
    # Read the JSON script
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found.", file=sys.stderr)
        sys.exit(1)
        
    with open(args.input, 'r', encoding='utf-8') as f:
        try:
            payload = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON script: {e}", file=sys.stderr)
            sys.exit(1)

    print("Connecting to remote GPU server for TTS synthesis...")
    
    # We will use Paramiko to set up a local port forward.
    # Because FastAPI might not be exposed to 0.0.0.0 publicly on the remote,
    # or it's firewalled, an SSH tunnel is the most secure way.
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(host, port=port, username=user, password=password, timeout=10)
        
        # Start the FastAPI server on the remote if it's not running
        # We run it via nohup in the background if port 8000 is not tracked
        check_cmd = "netstat -tuln | grep 8000"
        stdin, stdout, stderr = ssh.exec_command(check_cmd)
        if not stdout.read():
            print("Remote API is not running. Starting FastTTS Server via Conda...")
            start_cmd = "source ~/miniconda3/etc/profile.d/conda.sh && conda activate chattts && cd /jhdx0003008/openclaw/skills/ChatTTS && export HTTP_PROXY= HTTPS_PROXY= ALL_PROXY= http_proxy= https_proxy= all_proxy= && nohup python app.py > api.log 2>&1 &"
            ssh.exec_command(start_cmd)
            # Give it time to load the 3GB Torch model into VRAM
            print("Waiting 15 seconds for ChatTTS models to load into GPU VRAM...")
            time.sleep(15)
        else:
            print("Remote GPU API is already running. Proceeding...")

        # SSH tunnel is tricky inline, so we'll just execute a curl command on the remote server 
        # and pipe the binary audio back. This avoids port-forwarding threading complexities.
        
        json_str = json.dumps({"dialogue": payload}).replace("'", "'\"'\"'") # Escape for bash single quotes
        
        print("Submitting script to remote ChatTTS API via curl...")
        
        # We send the request locally on the remote box via curl, bypassing any rogue environment proxies
        curl_cmd = f"export http_proxy= https_proxy= all_proxy= HTTP_PROXY= HTTPS_PROXY= ALL_PROXY= && curl -sSf -X POST http://127.0.0.1:8000/synthesize -H 'Content-Type: application/json' -d '{json_str}' --output /tmp/tts_out.wav"
        
        stdin, stdout, stderr = ssh.exec_command(curl_cmd)
        
        # Wait for command to finish (this might take a minute depending on script length)
        # We check exit status
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            print(f"Remote synthesis failed: {stderr.read().decode()}", file=sys.stderr)
            sys.exit(1)
            
        # Download the file via SFTP
        sftp = ssh.open_sftp()
        print(f"Downloading finished audio to {args.output}...")
        sftp.get("/tmp/tts_out.wav", args.output)
        sftp.close()
        
        print(f"Podcast successfully generated and saved to: {args.output}")

    except Exception as e:
        print(f"SSH/Transfer Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
