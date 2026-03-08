import argparse
import asyncio
import websockets
import time
import subprocess
import os
import wave
import io

async def play_audio_queue(audio_queue, silent=False):
    while True:
        out_file = await audio_queue.get()
        if out_file is None:
            break
        # 无缝阻塞播放
        if not silent:
            subprocess.run(["afplay", out_file])
        audio_queue.task_done()

async def stream_audio_file(input_wav, chunk_duration_sec, websocket, audio_queue):
    print(f"📡 拦截长音频文件: {input_wav} (窗口={chunk_duration_sec}s)")
    try:
        with wave.open(input_wav, 'rb') as wf:
            sr = wf.getframerate()
            channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            total_frames = wf.getnframes()
            chunk_frames = int(chunk_duration_sec * sr)
            
            chunk_index = 0
            
            while wf.tell() < total_frames:
                frames_to_read = min(chunk_frames, total_frames - wf.tell())
                audio_data = wf.readframes(frames_to_read)
                
                tmp_chunk_file = f"/tmp/v2v_chunk_in_{chunk_index}.wav"
                with wave.open(tmp_chunk_file, 'wb') as out_wf:
                    out_wf.setnchannels(channels)
                    out_wf.setsampwidth(sampwidth)
                    out_wf.setframerate(sr)
                    out_wf.writeframes(audio_data)
                
                with open(tmp_chunk_file, "rb") as f:
                    chunk_bytes = f.read()
                    
                print(f"  [{chunk_index}] 🚀 发射滑窗波形...")
                start_t = time.time()
                await websocket.send(chunk_bytes)
                await websocket.send(b"FLUSH")
                
                response_bytes = await websocket.recv()
                latency = time.time() - start_t
                if response_bytes.startswith(b"ERROR"):
                    break
                    
                out_file = f"/tmp/v2v_chunk_out_{chunk_index}.wav"
                with open(out_file, "wb") as f:
                    f.write(response_bytes)
                    
                print(f"  [{chunk_index}] ✅ 响应时间 {latency:.2f}s | 直接入队播放！")
                await audio_queue.put(out_file)
                
                chunk_index += 1
    except Exception as e:
        print(f"❌ 读取文件错误: {e}")

async def stream_audio_mic(chunk_duration_sec, websocket, audio_queue):
    print(f"🎤 麦克风全双工已开启! 持续每 {chunk_duration_sec}s 自动截断并双传...")
    chunk_index = 0
    try:
        while True:
            tmp_chunk_file = f"/tmp/v2v_mic_in_{chunk_index}.wav"
            print(f"  [{chunk_index}] 监听中 (正在录制{chunk_duration_sec}秒)....")
            
            # 使用 macOS 原生的 ffmpeg 调用硬件麦克风。需要 Terminal 具有麦克风权限。
            cmd = [
                "ffmpeg", "-y", "-loglevel", "error", "-f", "avfoundation", 
                "-i", ":0", "-t", str(chunk_duration_sec), 
                "-ar", "16000", "-ac", "1", tmp_chunk_file
            ]
            
            subprocess.run(cmd)
            
            if not os.path.exists(tmp_chunk_file):
                print("❌ 提取麦克风失败，请检查 FFmpeg 硬件权限。")
                break
                
            with open(tmp_chunk_file, "rb") as f:
                chunk_bytes = f.read()
                
            print(f"  [{chunk_index}] 🚀 已截获波形，投递 V2V 引擎...")
            start_t = time.time()
            await websocket.send(chunk_bytes)
            await websocket.send(b"FLUSH")
            
            response_bytes = await websocket.recv()
            latency = time.time() - start_t
            if response_bytes.startswith(b"ERROR"):
                break
                
            out_file = f"/tmp/v2v_chunk_out_{chunk_index}.wav"
            with open(out_file, "wb") as f:
                f.write(response_bytes)
                
            print(f"  [{chunk_index}] ✅ 同传落定 {latency:.2f}s | 骨传导入列发音。")
            await audio_queue.put(out_file)
            chunk_index += 1
            
    except KeyboardInterrupt:
        print("中止同传。")

async def str_v2v(input_wav, mode, chunk_sec=5.0, silent=False):
    uri = "ws://127.0.0.1:18200/v2v-stream"
    audio_queue = asyncio.Queue()
    play_task = asyncio.create_task(play_audio_queue(audio_queue, silent))
    
    try:
        async with websockets.connect(uri, open_timeout=100, ping_interval=None, ping_timeout=100) as websocket:
            if mode == 'file':
                await stream_audio_file(input_wav, chunk_sec, websocket, audio_queue)
            elif mode == 'mic':
                await stream_audio_mic(chunk_sec, websocket, audio_queue)
                
        await audio_queue.put(None)
        await play_task
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"❌ WebSocket物理隧道断裂: {e}")
    except Exception as e:
        print(f"❌ 通信错误: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="千字流式跨语种双向网关 V2V")
    parser.add_argument("--mode", choices=['file', 'mic'], required=True, help="file (长文本大录音) 或 mic (直接语音接驳)")
    parser.add_argument("--input", type=str, help="指定波形文件路径 (仅 file 模式可用)")
    parser.add_argument("--chunk_sec", type=float, default=6.0, help="滑窗步长(秒)")
    parser.add_argument("--silent", action="store_true", help="启用静默测试验证模式")
    args = parser.parse_args()
    
    if args.mode == 'file' and not args.input:
        parser.error("文件直传模式必须附带 --input 参数")
        
    if not (2.0 <= args.chunk_sec <= 8.0):
        parser.error(f"SOP 黑名单拦截：拒绝 {args.chunk_sec} 秒的滑窗！为了保护远端 GPU 显存，切片参数被强制限制在 [2.0秒 - 8.0秒] 区间。")
        
    asyncio.run(str_v2v(args.input, args.mode, args.chunk_sec, args.silent))
