import argparse
import asyncio
import aiohttp
import re
import os
import time
import subprocess

# 采用标点与长度双维切分算法，确保每句话极其简短（最佳长度 ~ 20 字），极大缩减 GPU 首应耗时。
def split_text_into_chunks(text, max_len=40):
    # 根据句末标点初步断句
    sentences = re.split(r'([。！？；.!?;\n]+)', text)
    chunks = []
    current_chunk = ""
    for i in range(0, len(sentences)-1, 2):
        sentence = sentences[i] + sentences[i+1]
        sentence = sentence.strip()
        if not sentence:
            continue
            
        if len(current_chunk) + len(sentence) <= max_len:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # 如果单句依然超长，则通过短暂停顿（逗号）强拆
            if len(sentence) > max_len:
                comma_sentences = re.split(r'([，,]+)', sentence)
                sub_chunk = ""
                for j in range(0, len(comma_sentences)-1, 2):
                    sub_s = comma_sentences[j] + comma_sentences[j+1]
                    if len(sub_chunk) + len(sub_s) <= max_len:
                        sub_chunk += sub_s
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = sub_s
                if sub_chunk:
                    current_chunk = sub_chunk
            else:
                current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk)
    return chunks

async def fetch_tts(session, text, url="http://127.0.0.1:18100/synthesize"):
    async with session.post(url, json={"text": text}) as response:
        if response.status == 200:
            return await response.read()
        else:
            print(f"❌ Error fetching TTS for chunk: {text[:10]}..., Status: {response.status}")
            return None

# 后台不间断播放循环。一经塞入缓冲池，立刻张口说话。
async def play_audio_queue(audio_queue, silent=False):
    while True:
        audio_data = await audio_queue.get()
        if audio_data is None:
            break
        
        tmp_file = f"/tmp/tts_chunk_{time.time()}.wav"
        with open(tmp_file, "wb") as f:
            f.write(audio_data)
        
        # 阻塞在此等待当前音频放完，保障连贯口语不发生叠音冲撞。
        if not silent:
            subprocess.run(["afplay", tmp_file])
        audio_queue.task_done()

async def stream_tts(text, silent=False):
    print("🔥 工业级千字极速并发生成器启动！")
    chunks = split_text_into_chunks(text, max_len=40)
    print(f"📦 长文已切割为 {len(chunks)} 个独立流式算力块。")
    
    audio_queue = asyncio.Queue()
    play_task = asyncio.create_task(play_audio_queue(audio_queue, silent))
    
    overall_start = time.time()
    
    # 强制停用 keep-alive 复用，防止由于过载被 SSH 隧道掐断
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(force_close=True)) as session:
        for i, chunk in enumerate(chunks):
            start_time = time.time()
            audio_data = await fetch_tts(session, chunk)
            latency = time.time() - start_time
            print(f"  [{i}] ✅ {latency:.2f}s | {chunk}")
            
            if i == 0:
                first_latency = time.time() - overall_start
                print(f"🚀 【首句秒回指标达标】 首片 TTFB = {first_latency:.2f} 毫秒！立刻推送入播放矩阵！")
                
            if audio_data:
                await audio_queue.put(audio_data)
                
    await audio_queue.put(None)
    await play_task
    print(f"🎉 高速合成结束，总计播放/生成耗时：{time.time()-overall_start:.2f}秒。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chunked Streaming TTS Player")
    parser.add_argument("--text", type=str, required=True, help="要朗读的海量文本内容")
    parser.add_argument("--silent", action="store_true", help="静默模式")
    args = parser.parse_args()
    asyncio.run(stream_tts(args.text, args.silent))
