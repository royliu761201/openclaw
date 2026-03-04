import argparse
import asyncio
import sys
import os

try:
    import websockets
except ImportError:
    print("❌ Fatal: The 'websockets' python library is required for the V2V Streaming Tunnel.")
    print("Please run: pip install websockets")
    sys.exit(1)

async def stream_audio(input_file, output_file):
    uri = "ws://127.0.0.1:18200/v2v-stream"
    print(f"🔗 Establishing Ultra-Low Latency WebSocket to {uri} ...")
    
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        sys.exit(1)
        
    try:
        async with websockets.connect(uri, max_size=None, ping_interval=None) as websocket:
            print(f"📡 Socket bound! Pumping audio: {input_file}")
            
            # Read file in chunks to simulate streaming (or just dump it if it's a file)
            # Since this is a file-to-file script (wrapping the streaming backbone),
            # we send the whole file as a massive chunk and trigger FLUSH immediately.
            with open(input_file, "rb") as f:
                data = f.read()
            
            # Push audio bytes
            await websocket.send(data)
            # Push FLUSH command to trigger SeamlessM4T buffer execution
            await websocket.send(b"FLUSH")
            
            print("⏳ Awaiting stream return from cuda:1 ...")
            
            # Receive generated audio chunk
            result_bytes = await websocket.recv()
            
            import subprocess
            import tempfile
            
            # Write raw PCM/WAV to a temporary file first
            fd, temp_wav_path = tempfile.mkstemp(suffix=".wav")
            with os.fdopen(fd, "wb") as f:
                f.write(result_bytes)
                
            print(f"✅ V2V Success! Received {len(result_bytes)} bytes of translated PCM/WAV.")
            
            # Automatically convert to OpenClaw/Feishu native .opus representation
            if output_file.endswith('.opus') or output_file.endswith('.ogg'):
                print(f"🔄 Transcoding to native Feishu voice message format ({output_file})...")
                # Suppress ffmpeg output but keep errors
                cmd = ["/opt/homebrew/bin/ffmpeg", "-y", "-i", temp_wav_path, "-c:a", "libopus", "-b:a", "64k", output_file]
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    print(f"✅ Transcoded successfully to {output_file}")
                except Exception as e:
                    print(f"⚠️ Warning: ffmpeg transcoding failed: {e}. Falling back to copying raw wav.")
                    import shutil
                    shutil.copy(temp_wav_path, output_file)
            else:
                import shutil
                shutil.copy(temp_wav_path, output_file)
                
            os.remove(temp_wav_path)
            
    except Exception as e:
        print(f"❌ WebSocket Tunnel Failure: {e}")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Local Client for Meta Seamless Streaming V2V Tunnel.")
    parser.add_argument("--input", required=True, help="Input wav file path (foreign language).")
    parser.add_argument("--output", required=True, help="Output opus/wav file path (Chinese translation).")
    args = parser.parse_args()
    
    asyncio.run(stream_audio(args.input, args.output))
