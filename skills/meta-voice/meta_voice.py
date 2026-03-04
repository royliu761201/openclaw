import os
import sys
import argparse
import asyncio
import shutil
import time

# Add ResearchBot to path to use its skills
PROJECT_ROOT = "/Users/roy-jd/Documents/projects/ResearchBot"
if PROJECT_ROOT not in sys.path:
    sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from skills.ssh_executor import SSHExecutor

async def run_meta_v2v():
    parser = argparse.ArgumentParser(description="Professional Meta V2V API Wrapper.")
    parser.add_argument("--input", required=True, help="Input wav file for V2V.")
    parser.add_argument("--output", required=True, help="Local output wav path.")
    parser.add_argument("--tgt_lang", default="cmn", help="Target language (default: Mandarin).")
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

    print(f"📡 Connecting to GPU server for Meta V2V Translation via API...")

    remote_in_path = f"/tmp/v2v_in_{int(time.time())}.wav"
    remote_out_path = f"/tmp/v2v_out_{int(time.time())}.wav"
    remote_status_path = f"/tmp/v2v_status_{int(time.time())}.txt"
    
    # 1. Upload input audio
    await executor.push_file(args.input, remote_in_path)

    # 2. Trigger API conversion on the remote server
    # Assuming the API is running on port 8001
    cmd = f"nohup sh -c 'curl --noproxy \"*\" -s -w \"\\n%{{http_code}}\" -X POST http://127.0.0.1:8001/v2v -F \"audio_file=@{remote_in_path}\" -F \"tgt_lang={args.tgt_lang}\" --output {remote_out_path} > {remote_status_path} 2>&1' > /dev/null 2>&1 &"
    await executor.shell.execute(cmd)

    print("🚀 Sending request to V2V GPU Backend...")
    print("⏳ Waiting for translation to complete...")
    
    timeout = 600
    start_time = time.time()
    success = False
    
    while time.time() - start_time < timeout:
        # Check status file dynamically
        res = await executor.shell.execute(f"cat {remote_status_path}")
        content = res.get("stdout", "").strip()
        if content:
            lines = content.split('\n')
            if len(lines[-1].strip()) == 3 and lines[-1].strip().isdigit():
                if lines[-1].strip() == "200":
                    success = True
                else:
                    print(f"❌ Server returned HTTP Code: {lines[-1].strip()}")
                break
        await asyncio.sleep(5)

    if success:
        print(f"⬇️ Downloading result...")
        # Clean up existing dir to ensure fresh copy
        remote_out_dir = "/tmp/v2v_out_dir"
        await executor.shell.execute(f"rm -rf {remote_out_dir} && mkdir -p {remote_out_dir} && mv {remote_out_path} {remote_out_dir}/result.wav")
        
        local_temp_dir = "/tmp/v2v_local_temp"
        os.makedirs(local_temp_dir, exist_ok=True)
        await executor.download_results(remote_out_dir, local_temp_dir)
        
        dl_path = f"{local_temp_dir}/v2v_out_dir/result.wav"
        if os.path.exists(dl_path):
            shutil.copy(dl_path, args.output)
            print(f"✅ Success! Saved V2V result to {args.output}")
            
            # Cleanup remote payloads
            await executor.shell.execute(f"rm -f {remote_in_path} {remote_status_path}")
        else:
            print(f"❌ Result file not found in downloaded folder")
    else:
        print(f"❌ V2V Translation failed or timed out. Make sure the API is running on port 8001.")

if __name__ == "__main__":
    asyncio.run(run_meta_v2v())
