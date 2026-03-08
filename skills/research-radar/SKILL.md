---
name: research-radar
description: 24/7 Autonomous Research Radar for continuous tracking of academic frontiers.
metadata: { "openclaw": { "emoji": "📡", "requires": { "bins": ["python3"] } } }
---

# Research Radar Skill (V3: Decoupled Architecture)

An autonomous, Git-SSoT-driven surveillance system utilizing `academic-search` to track cutting-edge research targets defined in the `05_RESEARCH_RADAR_PDCA.md` plan.

## Purpose

To eradicate manual literature monitoring while ensuring absolute data security and zero latency impact on the primary Node 01. The radar pipeline is purely decoupled into a **Producer (Scraper)** and a **Consumer (Brain)**.

## Core Mechanisms (The Git-SSoT Pipeline)

1. **⛏️ The Producer (`scripts/radar_collector.py`)**:
   - Deployed **exclusively on Node 02**.
   - Runs silently via cron. It is a powerful **Tri-Engine Scraper (ArXiv, Tavily, Exa)** that blindly scrapes raw academic abstracts, deep web news, and GitHub code snippets.
   - It dumps the combined intelligence into `workspace/docs/research_ideation/radar_raw_data/YYYY-MM-DD_RAW.md`.
   - Has absolutely **no access** to LLM APIs, preventing credential leakage and compute overhead. It strictly commits and pushes to Git.

2. **🧠 The Consumer (`scripts/radar_analyzer.py` & `radar_manual.py`)**:
   - Deployed **exclusively on Node 01** (The Brain).
   - Python scripts **ABSOLUTELY DO NOT** call LLM APIs directly (Zero Blind Token Burn).
   - They pull raw `.md` files, cross-reference the rigidly-hardcoded `pi_profile_xiaohua_liu.md` and Idea List, and bundle them into an **Inbox Prompt**.
   - Generates an `_INBOX.md` file in `radar_reports/`. Dandan (Agent) then reads this inbox and performs the 4-stage cognitive swarming (Triage, Red Team, Blue Team, Ranger) natively. User can view the token burn in real-time.

## Usage

**On Edge Node (02)** - Pure Collection:

```bash
python3 scripts/radar_collector.py --sectors CaLaM Frenet
```

**On Brain Node (01)** - Cognitive Analysis:

```bash
python3 scripts/radar_analyzer.py --date 2026-03-07
```

## 🎯 核心使用场景与 PI 日常操作 (Usage Scenarios & Daily Workflow)

作为一项**综合型元技能 (Meta-Skill)**，雷达已经完全融入了您的日常科研节律。以下是全套操作指南：

### 🛠️ 1. 如何定制雷达目标？(Target Customization)
雷达采用**完全剥离的配置库**，您不需要修改任何一行 Python 代码。
**唯一操作点**: 直接打开并编辑 `~/workspace/docs/research_ideation/radar_targets.json`。
- **改关键词**: 在 `radar_keywords` 字典里，增加您突然感兴趣的小分支（例如量子退火）。
- **盯防对手**: 在 `top_scholars` 数组里加上新的名字（比如刚刚跳槽去 xAI 的核心员工），雷达就会自动锁定他。
由于**Git-as-SSoT**的机制，只要您在这台电脑上改了 JSON 并推送到 Git，远端负责抓取苦力的 Node 02 明天早上就会自动下载最新的暗杀名单执行！

### 🌅 2. 首席总指挥的每日清晨剧本 (The Boss's Daily Workflow)
雷达是极其安静的，它的设计初衷就是**不占用您的工作终端算力和注意力**。

**08:00 AM (Edge Node 02 苦力作业)**
1. Node 02 在海外通过定时任务醒来。它拉取您最新配置的 `radar_targets.json`。
2. 它伪装成真实用户，挂着 15 秒的反封锁间隙，在 arXiv、Tavily、Exa 上狂刷几百篇最新的论文、技术博客和 GitHub 源码。
3. 它把这些“生肉”通过 Git 静默推送到总部的 `radar_raw_data/`。

**09:00 AM (您的行动节点 - Node 01)**
1. 您端着咖啡坐到电脑前。您可以在命令行打一句：`执行雷达大脑分析` 或者 `python3 scripts/radar_analyzer.py`。
2. **多兵团出击 (The Swarm)**: 
   - **Triage Agent (过滤网)** 瞬间审阅 Node 02 昨晚发回的几百篇生肉。如果全是水文，直接丢弃，不弹任何通知恶心您；
   - 过滤网如果抓到了 1 篇真干货：立刻放手让 **Red Team (找茬算公式)**、**Blue Team (谋划抄源码)** 和 **Ranger (寻找生物/物理跨界方案)** 一起上阵辩论。
3. **战报送达**: 您最终只需打开 `workspace/docs/research_ideation/radar_reports/` 目录下的当日报告。里面**不要看摘要**，直接看 Red/Blue/Ranger 的辩论和给您的 `Micro-PoC` 建议。您根据报告，直接去分配任务给下属或亲自验证那个 PoC。

### 🛡️ 3. 核心护城河防御战 (Idea Defense Mechanism)
如果您的 `EXTENSION_IDEA_MASTER.md` 里躺着一个绝妙的想法，迟迟没来得及发论文。雷达会死死的盯着这个关键词组合。如果有任何名不见经传的学校突然发了一篇类似思路的预印本，Triage Agent 会将其标记为 **`[X - Threat / 已抢夺]`** 并红色报警，提醒您立刻斩断当前实验，优先抢占发表！

### 🔄 4. 终极闭环：雷达如何实现 PDCA 进化？(The Feedback Loop)
总长，雷达的命脉在于**闭环 (Closed-Loop)**。它不是单向输出的喇叭，它依赖您的反馈来完成 PDCA 的最后一个 **A (Act / 固化)** 动作：
1. **正反馈 (Idea 落地)**: 如果您觉得雷达今天给的跨界点子（比如用量子力学解算 Burgers 方程）很绝，您只需在聊天中对我说：*“把今天雷达提的量子 Burger 想法加入扩展清单”*。我就会立刻将其写入 `EXTENSION_IDEA_MASTER.md`，它正式成为我们下一步要啃的硬骨头。
2. **负反馈 (免疫接种)**: 如果雷达今天给了一个极其愚蠢的 CV（计算机视觉）水文，您只需要骂一句：*“以后雷达少给我推这种纯 CV 的垃圾！”*。**划重点：此时系统会引爆 `solidify` 技能！** 我会立刻将您的这句怒火转化为一条物理级的 **L3 Anti-Body (抗体)**，并硬编码进 `pi_profile_xiaohua_liu.md`。
**这就是真正的闭环：系统永远不会在同一个坑里摔倒两次。老板的每一次咒骂，都会变成系统底层的一行正则约束。**

### 🚫 防坑禁区 (Anti-Hallucination)
- **The Grounding Law for Radar Associations**: When linking external research to internal `EXTENSION_IDEA_MASTER.md` items or existing papers, the Radar Brain Agent must NEVER guess the internal project scope based purely on title similarity. You MUST first physically query `workspace/docs/system_core/09_GROUNDED_PAPER_INDEX.md` or the corresponding SSoT to ensure the internal context being compared against is factually correct.
