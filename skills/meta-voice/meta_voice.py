import os
import sys
import argparse
import asyncio
import json
import shutil

# Add ResearchBot to path to use its skills
PROJECT_ROOT = "/Users/roy-jd/Documents/projects/ResearchBot"
if PROJECT_ROOT not in sys.path:
    sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from skills.ssh_executor import SSHExecutor

async def run_meta_v2v():
    parser = argparse.ArgumentParser(description="Professional Meta V2V Skill wrapper.")
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

    print(f"📡 Connecting to GPU server for Meta V2V Translation...")

    remote_script_path = "/tmp/remote_entrypoint_v2v.py"
    local_script_path = os.path.join(os.path.dirname(__file__), "remote_entrypoint.py")
    
    # Upload script
    await executor.push_file(local_script_path, remote_script_path)

    remote_in_path = "/tmp/meta_v2v_in.wav"
    remote_out_dir = "/tmp/meta_v2v_out_dir"
    remote_out_path = f"{remote_out_dir}/result.wav"
    
    # Upload input and prepare out dir
    await executor.push_file(args.input, remote_in_path)
    await executor.shell.execute(f"rm -rf {remote_out_dir} && mkdir -p {remote_out_dir}")

    # Engineering Standard: Use dedicated conda env
    python_bin = "/root/miniconda3/envs/v2v/bin/python"
    inner_cmd = f"{python_bin} {remote_script_path} --action v2v --input {remote_in_path} --output {remote_out_path} --tgt_lang {args.tgt_lang}"

    print(f"🚀 Executing Meta V2V Translation...")
    exit_code, stdout, stderr = await executor.run_in_env("v2v", inner_cmd)
    
    if exit_code == 0:
        local_temp_dir = "/tmp/meta_v2v_local_temp"
        os.makedirs(local_temp_dir, exist_ok=True)
        await executor.download_results(remote_out_dir, local_temp_dir)
        
        dl_path = f"{local_temp_dir}/meta_v2v_out_dir/result.wav"
        if os.path.exists(dl_path):
            shutil.copy(dl_path, args.output)
            print(f"✅ Success! Saved V2V result to {args.output}")
        else:
            print(f"❌ Result file not found in downloaded folder")
    else:
        print(f"❌ Remote execution failed (Exit Code: {exit_code})")
        if stderr: print(f"Error: {stderr}")

if __name__ == "__main__":
    asyncio.run(run_meta_v2v())
