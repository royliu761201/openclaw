import argparse
import urllib.request
import json
import sys
import os

def run_tts(text, output_path, speed=5):
    url = "http://127.0.0.1:18100/tts"
    payload = json.dumps({"text": text, "speed": speed}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, method='POST')
    req.add_header('Content-Type', 'application/json')
    
    print(f"📡 Sending text to local proxy tunnel -> GPU ChatTTS ({url})...")
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            if response.status == 200:
                import tempfile
                import subprocess
                import shutil
                if output_path.endswith('.opus') or output_path.endswith('.ogg'):
                    fd, temp_wav_path = tempfile.mkstemp(suffix=".wav")
                    with os.fdopen(fd, 'wb') as out_file:
                        out_file.write(response.read())
                    print(f"🔄 Transcoding to native Feishu voice message format ({output_path})...")
                    cmd = ["/opt/homebrew/bin/ffmpeg", "-y", "-i", temp_wav_path, "-c:a", "libopus", "-b:a", "64k", output_path]
                    try:
                        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"✅ Success! Saved generated audio to {output_path}")
                    except Exception as e:
                        print(f"⚠️ Warning: ffmpeg transcoding failed: {e}. Saving as raw wav.")
                        shutil.copy(temp_wav_path, output_path)
                    os.remove(temp_wav_path)
                else:
                    with open(output_path, 'wb') as out_file:
                        out_file.write(response.read())
                    print(f"✅ Success! Saved generated audio to {output_path}")
            else:
                print(f"❌ Server returned status code: {response.status}")
                sys.exit(1)
    except Exception as e:
        print(f"❌ Complete failure communicating with TTS daemon: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local Client for Remote ChatTTS via Tunnel.")
    parser.add_argument("--text", required=True, help="Text to synthesize.")
    parser.add_argument("--output", required=True, help="Local output wav path.")
    parser.add_argument("--speed", type=int, default=5, help="Speed of speech (1-10).")
    args = parser.parse_args()
    
    run_tts(args.text, args.output, args.speed)
