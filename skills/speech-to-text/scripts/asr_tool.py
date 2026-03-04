#!/usr/bin/env python3
import subprocess
import argparse
import sys
import os

def run_cmd(cmd, check=True, capture_output=False):
    if capture_output:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and res.returncode != 0:
            print(f"❌ 命令失败: {cmd}\nError: {res.stderr}")
            sys.exit(1)
        return res.stdout
    else:
        res = subprocess.run(cmd, shell=True)
        if check and res.returncode != 0:
            sys.exit(1)
        return res.returncode

def main():
    parser = argparse.ArgumentParser(description="OpenClaw ASR (Speech-to-Text) Tool - M1 Optimized")
    parser.add_argument("audio_path", help="Local path to the .wav audio file")
    parser.add_argument("--model", default="large-v3-turbo-q5_0", help="Model name")
    parser.add_argument("--language", default="zh", help="Language code (zh, en)")
    
    args = parser.parse_args()
    
    audio_path = os.path.abspath(args.audio_path)
    filename = os.path.basename(audio_path)
    remote_host = "roy-002"
    remote_base = "~/.openclaw_deps/whisper.cpp-1.6.2"
    remote_audio = f"/tmp/{filename}"
    model_path = f"{remote_base}/models/ggml-{args.model}.bin"
    
    if not os.path.exists(audio_path):
        print(f"❌ 找不到本地音频文件: {audio_path}")
        sys.exit(1)

    print(f"📤 [1/3] 上传音频至 Mac 02...")
    run_cmd(f"scp -o StrictHostKeyChecking=no {audio_path} {remote_host}:{remote_audio}")

    print(f"⚡ [2/3] 启动 M1 原生 ASR 推理 (Apple Accelerate)...")
    # whisper.cpp command: -m [model] -f [file] -l [lang] -nt (no timestamps)
    asr_cmd = f"ssh -o StrictHostKeyChecking=no {remote_host} \"{remote_base}/main -m {model_path} -f {remote_audio} -l {args.language} -nt\""
    
    result = run_cmd(asr_cmd, capture_output=True)
    
    print(f"🧹 [3/3] 远程现场清理...")
    run_cmd(f"ssh -o StrictHostKeyChecking=no {remote_host} \"rm -f {remote_audio}\"")

    print("\n--- 识别结果 ---")
    print(result.strip())
    print("----------------\n")

if __name__ == "__main__":
    main()
