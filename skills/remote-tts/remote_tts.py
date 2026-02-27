import os
import sys
import argparse
import asyncio
import json
import shutil
import time

# Add ResearchBot to path to use its skills
PROJECT_ROOT = "/Users/roy-jd/Documents/projects/ResearchBot"
if PROJECT_ROOT not in sys.path:
    sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from skills.ssh_executor import SSHExecutor

async def run_remote_tts():
    parser = argparse.ArgumentParser(description="Professional Specialized TTS Skill wrapper.")
    parser.add_argument("--text", required=True, help="Text to synthesize.")
    parser.add_argument("--output", required=True, help="Local output wav path.")
    args = parser.parse_args()

    # Engineering Standard: Use SSHExecutor from ResearchBot
    remote_config = {
        "host": os.environ.get('SSH_HOST'),
        "port": int(os.environ.get('SSH_PORT', 22)),
        "user": os.environ.get('SSH_USER'),
        "pass": os.environ.get('SSH_PASS')
    }
    
    executor = SSHExecutor(config={"remote": remote_config})
    executor.shell.config = remote_config
    executor.transfer.config = remote_config

    print(f"📡 Connecting to GPU server for Specialized TTS synthesis...")

    remote_payload_path = "/tmp/tts_payload.json"
    remote_out_path = "/tmp/tts_out.wav"
    remote_status_path = "/tmp/tts_status.txt"
    
    # 1. Prepare and upload payload
    payload = {"dialogue": [{"speaker": "host", "text": args.text}]}
    with open("/tmp/local_payload.json", "w") as f:
        json.dump(payload, f)
    await executor.push_file("/tmp/local_payload.json", remote_payload_path)

    # 2. Trigger async synthesis via remote engine (assumes API is running on 8000)
    # This follows the existing logic but uses the standardized executor
    cmd = f"nohup sh -c 'curl --noproxy \"*\" -s -w \"\\n%{{http_code}}\" -X POST http://127.0.0.1:8000/synthesize -H \"Content-Type: application/json\" -d @{remote_payload_path} --output {remote_out_path} > {remote_status_path} 2>&1' > /dev/null 2>&1 &"
    await executor.shell.execute(cmd)

    print("⏳ Waiting for generation...")
    timeout = 600
    start_time = time.time()
    success = False
    
    while time.time() - start_time < timeout:
        # Check status file
        res = await executor.shell.execute(f"cat {remote_status_path}")
        content = res.get("stdout", "").strip()
        if content:
            lines = content.split('\n')
            if len(lines[-1].strip()) == 3 and lines[-1].strip().isdigit():
                if lines[-1].strip() == "200":
                    success = True
                break
        await asyncio.sleep(5)

    if success:
        print(f"⬇️ Downloading result...")
        # Since pull_directory is preferred in the skill, we use a temp dir
        remote_out_dir = "/tmp/tts_out_dir"
        await executor.shell.execute(f"mkdir -p {remote_out_dir} && cp {remote_out_path} {remote_out_dir}/result.wav")
        
        local_temp_dir = "/tmp/tts_local_temp"
        os.makedirs(local_temp_dir, exist_ok=True)
        await executor.download_results(remote_out_dir, local_temp_dir)
        
        dl_path = f"{local_temp_dir}/tts_out_dir/result.wav"
        if os.path.exists(dl_path):
            shutil.copy(dl_path, args.output)
            print(f"✅ Success! Saved TTS result to {args.output}")
    else:
        print(f"❌ Synthesis failed or timed out.")

if __name__ == "__main__":
    asyncio.run(run_remote_tts())
