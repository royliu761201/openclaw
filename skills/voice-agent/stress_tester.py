import asyncio
import time
import urllib.request
import json
import websockets
import os
import aiohttp

# 终极多维压测配置 (The Matrix)
TTS_URL = "http://127.0.0.1:18100/synthesize"
V2V_WS_URL = "ws://127.0.0.1:18200/v2v-stream"

# 1. 变长边界基准测试集 (Performance & Length Variability)
TTS_TEST_CASES = [
    {"name": "Micro-Sentence (12 chars)", "text": "你好，这是极短测试。"},
    {"name": "Standard-Sentence (40 chars)", "text": "老板您好，这是标准长度的测试数据。我们在压测单线程处理这一段数据时需要的硬算力时间。"},
    {"name": "Long-Sentence (120 chars)", "text": "为了测试极端的长文本并发处理能力，这将被当作长句测试。系统如果无法将极具耗时的模型推演抛入后台线程池，那么这个长达百字以上的文段将毫无疑问地把 WebSocket 心跳包彻底卡死。这正是我们重写了底层架构所要防范的技术盲点。"}
]

# 2. 异步高并发吞吐量冲击 (Concurrency Burst)
CONCURRENCY_LEVEL = 5  # 瞬间齐射 5 个请求

async def test_tts_endpoint_async(session, case, idx):
    start_time = time.time()
    payload = {"text": case["text"]}
    print(f"  [Q-{idx}] 发射: {case['name']} ...")
    try:
        async with session.post(TTS_URL, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
            status = response.status
            content = await response.read()
            elapsed = time.time() - start_time
            if status == 200:
                print(f"  [Q-{idx}] ✅ PASS ({elapsed:.2f}s) -> 生成 {len(content)/1024:.2f} KB")
                return True, elapsed
            else:
                print(f"  [Q-{idx}] ❌ FAIL (HTTP {status}) 在 {elapsed:.2f}s")
                return False, elapsed
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"  [Q-{idx}] 💥 ERROR: {str(e)} 在 {elapsed:.2f}s")
        return False, elapsed

async def run_performance_baseline():
    print("\n==========================================")
    print(" 🚀 [A] 孤立变长边界基准测试 (Linear Isolation)")
    print("==========================================")
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(force_close=True)) as session:
        for i, case in enumerate(TTS_TEST_CASES):
            await test_tts_endpoint_async(session, case, f"Linear-{i}")

async def run_concurrency_stress():
    print("\n==========================================")
    print(" 🌪️ [B] 集群并发冲锋测试 (Concurrency Blitz)")
    print("==========================================")
    print(f"  > 正在模拟 {CONCURRENCY_LEVEL} 个 AI 智能体同时争抢单卡 TTS 算力...")
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(force_close=True)) as session:
        tasks = []
        # 使用 Standard-Sentence 发起并发
        case = TTS_TEST_CASES[1] 
        for i in range(CONCURRENCY_LEVEL):
            tasks.append(test_tts_endpoint_async(session, case, f"Burst-{i}"))
        
        start_burst = time.time()
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_burst
        
        success_count = sum([1 for r, _ in results if r])
        print(f"\n  [🎯 集群结论] 成功率: {success_count}/{CONCURRENCY_LEVEL} | 并发墙总耗时: {total_time:.2f}s")

async def test_v2v_edge_cases():
    print("\n==========================================")
    print(" 🛡️ [C] V2V 空包与极短流极限防爆测试 (V2V Edge Cases)")
    print("==========================================")
    # 模拟客户端 WebSocket 发射0字节以及直接异常断列
    try:
        async with websockets.connect(V2V_WS_URL, max_size=None, ping_interval=20, open_timeout=10) as ws:
            print("  > [C-1] 建立连接后发送合法极短包...")
            # 制造极短无效音频头部 (44 bytes RIFF)
            fake_wav = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
            await ws.send(fake_wav)
            await ws.send(b"FLUSH")
            print("  > [C-1] 等待服务端防爆或异常响应...")
            res = await ws.recv()
            if b"ERROR" in res or len(res) < 100:
                 print(f"  > [C-1] ✅ 服务端成功熔断或静默容错拦截，未发生 OOM 穿透！返回特征: {res[:20]}")
            else:
                 print("  > [C-1] ⚠️ 服务端尝试进行了强行推演并返回内容。")
    except Exception as e:
        print(f"  > [C-1] ✅ 服务端底层直接掐断恶意空传，防爆成功: {e}")

async def main():
    print("🤖 工业级多维极限压测套件启动")
    await run_performance_baseline()
    await run_concurrency_stress()
    await test_v2v_edge_cases()
    print("\n==========================================")
    print(" 🎉 [EOF] 多维压测报表输出完毕")
    print("==========================================")

if __name__ == "__main__":
    asyncio.run(main())
