#!/usr/bin/env python3
import os
import sys
import time
import argparse

# 0. L1 Sandbox Enforcement (Venv Execution Check)
VENV_PYTHON = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "venv", "bin", "python3")
if sys.executable != VENV_PYTHON and os.path.exists(VENV_PYTHON):
    print(f"🛑 [L1 Sandbox Alert] You are running this globally. Relaunching via sandboxed interpreter: {VENV_PYTHON}")
    os.execl(VENV_PYTHON, VENV_PYTHON, *sys.argv)

def parse_args():
    parser = argparse.ArgumentParser(description="Kokoro TTS Zero-Footprint CLI (Node 01/02)")
    parser.add_argument("--text", type=str, required=True, help="Text to synthesize (Multilingual supported)")
    parser.add_argument("--output", type=str, required=True, help="Output .wav path")
    parser.add_argument("--voice", type=str, default="af_heart", help="Voice profile name")
    parser.add_argument("--speed", type=float, default=1.0, help="Speech speed multiplier")
    parser.add_argument("--dry-run", action="store_true", help="Perform synthesis but save to /tmp and delete immediately (Zero-Interference Testing)")
    return parser.parse_args()

def main():
    # 1. 遵守 L1 Constitution: 强制底进程隔离 (The `nice` Protocol)
    # Ensuring OS level demotion so it never interrupts the host's IDE/Browser.
    try:
        os.nice(19)
    except Exception as e:
        print(f"⚠️ Notice: Could not demote process nice level: {e}")

    args = parse_args()
    start_time = time.time()

    # 2. 延迟加载 (Lazy Import) - Keep CLI --help zero-latency
    try:
        from kokoro_onnx import Kokoro
        import soundfile as sf
    except ImportError:
        print("❌ Error: Dependencies missing. Please run `pip install kokoro-onnx soundfile`")
        sys.exit(1)

    # 3. 定位隔离沙盒内的模型 (Sandbox Resolution)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    model_path = os.path.join(base_dir, "models", "kokoro-v1.0.onnx")
    voices_bin = os.path.join(base_dir, "models", "voices-v1.0.bin")

    if not os.path.exists(model_path):
        print(f"❌ Error: ONNX model not found at {model_path}. Run download_model.py first.")
        sys.exit(1)

    voices_path = voices_bin

    # 4. Engine Initialization
    try:
        kokoro = Kokoro(model_path, voices_path)
    except Exception as e:
        print(f"❌ Error initializing Kokoro ONNX engine: {e}")
        sys.exit(1)

    # 5. Language detection (Basic fallback for CJK vs EN)
    has_chinese = any('\u4e00' <= char <= '\u9fff' for char in args.text)
    lang_code = "cmn" if has_chinese else "en-us"
    
    # Auto-switch to a Chinese voice if default English voice was provided
    if has_chinese and args.voice == "af_heart":
        args.voice = "zf_xiaoxiao"

    # 6. Inference Call
    print(f"⏳ Synthesizing text (lang: {lang_code})...")
    try:
        samples, sample_rate = kokoro.create(args.text, voice=args.voice, speed=args.speed, lang=lang_code)
    except Exception as e:
        print(f"❌ Error during inference: {e}")
        sys.exit(1)

    # 7. Output Routing & Dry-Run Enforcement
    output_path = args.output
    if args.dry_run:
        output_path = f"/tmp/kokoro_dry_run_{int(time.time())}.wav"
        print(f"🚧 [Dry-Run] Rerouting output to volatile storage: {output_path}")

    try:
        sf.write(output_path, samples, sample_rate)
    except Exception as e:
        print(f"❌ Error writing output file: {e}")
        sys.exit(1)

    elapsed_time = time.time() - start_time
    print(f"✅ Success! Synthesis completed in {elapsed_time:.2f}s (Benchmark: < 2.5s)")
    print(f"💾 Saved to {output_path}")

    # 8. Dry-Run Cleanup (Zero-Footprint Law)
    if args.dry_run:
        print(f"🧹 [Dry-Run] Erasing volatile file: {output_path}")
        os.remove(output_path)
        print(f"🛑 [Dry-Run] Execution terminated cleanly. No artifacts left.")

if __name__ == "__main__":
    main()
