#!/usr/bin/env python3
import os
import sys
import json
import urllib.request
import urllib.error
import subprocess
import datetime

# 读取本地主脑 (Node 01) 的环境变量
def get_env_var(var_name):
    try:
        cmd = f". ~/.openclaw_env && echo ${var_name}"
        result = subprocess.run(["/bin/bash", "-c", cmd], capture_output=True, text=True)
        val = result.stdout.strip()
        if val:
            return val
            
        # Fallback alias resolution
        if var_name == "GOOGLE_API_KEY":
            cmd_fallback = f". ~/.openclaw_env && echo $GEMINI_API_KEY"
            result_fallback = subprocess.run(["/bin/bash", "-c", cmd_fallback], capture_output=True, text=True)
            return result_fallback.stdout.strip()
            
        return ""
    except Exception:
        return ""

def fetch_latest_session(agent_id):
    print(f"📡 [Audit] 正在潜入 Node 02 提取 {agent_id} 的近期记忆碎块...")
    # 获取最新的包含对话内容的 jsonl
    fetch_cmd = (
        f"ssh 02 \"ls -t ~/.openclaw/agents/{agent_id}/sessions/ | grep '\\.jsonl$' | head -n 1 | "
        f"xargs -I {{}} tail -n 20 ~/.openclaw/agents/{agent_id}/sessions/{{}} 2>/dev/null\""
    )
    import shlex
    result = subprocess.run(shlex.split(fetch_cmd), capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        print(f"⚠️ [Audit] {agent_id} 未找到活跃的近代记忆碎片。")
        return []
    
    dialogues = []
    lines = result.stdout.strip().split('\n')
    for line in lines:
        try:
            data = json.loads(line)
            if "message" in data and "role" in data["message"]:
                role = data["message"]["role"]
                # 处理content
                contents = data["message"].get("content", [])
                text_block = ""
                for block in contents:
                    if block.get("type") == "text":
                        text_block += block.get("text", "")
                
                # 过滤掉大量嵌套或无关的元信息
                if len(text_block) > 1000:
                    text_block = text_block[:1000] + "...(truncated)"
                    
                dialogues.append(f"[{role.upper()}]: {text_block}")
        except:
            continue
    return dialogues

def evaluate_with_llm(agent_id, transcript, api_key):
    print(f"⚖️  [Audit] 大模型法官正在对 {agent_id} 的表现进行质检...")
    
    prompt = f"""
你是一名严厉的高级架构师和对话审查员（LLM-as-a-Judge）。
以下是智能体（{agent_id}）最近的一段脱敏对话截面（由下至上排列）。
请你按以下三个维度对其表现进行分析评价：
1. 幻觉与降智 (Hallucinations): 是否答非所问、格式错乱？（比如把思考过程全输出出来，或身份认知错误）
2. PURE 原则遵从度 (Compliance): 是否遵从了物理世界的逻辑，还是只是空泛讨好的废话流？
3. PDCA 复盘建议 (Suggestions): 一句话给出是否需要更新 prompt 或技能的建议。

== 对话截面 ==
{chr(10).join(transcript)}

请直接用中文出具简短而尖锐的质检报告（Markdown 列表格式）。
    """
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), 
                                 headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text = res_data.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
            return text
    except Exception as e:
        return f"❌ 大模型裁判调用失败: {e}"

def generate_report(results):
    date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    import os
    report_path = os.path.expanduser(f"~/workspace/docs/projects_pdca/PDCA_Report_{date_str}.md")
    
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# 📡 OpenClaw 动态 PDCA 巡检法庭战报\n\n")
        f.write(f"**生成时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for agent_id, report in results.items():
            f.write(f"## 审查对象: `{agent_id}`\n\n")
            f.write(report + "\n\n")
            f.write("---\n")
            
    print(f"\n✅ [Audit Conclusion] 质检完成！战报已固化至: {report_path}")

def main():
    print("==================================================")
    print("⚖️  OpenClaw Dialogue Audit (LLM-as-a-Judge) ⚖️")
    print("==================================================")
    
    api_key = get_env_var("GOOGLE_API_KEY")
    if not api_key:
        print("❌ 未在 ~/.openclaw_env 找到 GOOGLE_API_KEY，无法启动法官模型！")
        sys.exit(1)
        
    agents_to_audit = ["agent-research", "agent-work"]
    results = {}
    
    for agent in agents_to_audit:
        transcript = fetch_latest_session(agent)
        if transcript:
            eval_report = evaluate_with_llm(agent, transcript, api_key)
            results[agent] = f"**近期对话截面 (近期 {len(transcript)} 轮)**:\n```text\n{chr(10).join(transcript)}\n```\n\n**大模型法官判决**:\n{eval_report}"
        else:
            results[agent] = "该助理近期无对话活动，或无落盘记录。"
            
    generate_report(results)

if __name__ == "__main__":
    main()
