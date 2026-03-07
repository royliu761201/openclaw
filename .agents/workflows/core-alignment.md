---
description: Execute the Core Alignment Protocol (The 5th Law) to perform deep physical and semantic auditing of the entire system.
---

# Core Alignment Protocol (核心对齐与深度固化剧本)

当老板下达 `/core-alignment` 指令，或者在系统发生重大跃迁后，你（作为执行 Agent）必须严格按照以下步骤履行**第五法则（05_SYSTEM_AUDIT_PROTOCOL）**。

本次对齐分为**物理底线扫描**与**大模型语义级对齐**双重攻防。

## 阶段一：物理外骨骼镇压 (Zero-Tolerance Physical Audit)

大模型的记忆不可靠，第一步绝对禁止你主观阅读。必须将低级易错的红线交由没脑子的机器探针去暴力排雷。

1. **执行雷达扫描**：
   使用 `run_command` 直接执行审计探针：
   ```bash
   python3 /Users/roy-jd/Documents/projects/openclaw/skills/skill-aligner/scripts/audit.py
   ```
2. **处理违宪警报**：
   如果脚本输出 `[FAILED]` 并列出了违规技能（如遗留了 `/root` 废旧路径，或缺失宪法声明显卡），你必须：
   - 使用 `view_file` 打开报错的 `SKILL.md`。
   - 使用 `replace_file_content` 动手术剜除坏死代码，并贴上宪法引用块。
   - **循环执行步骤 1**，直到整个物理世界输出：`✅ AUDIT PASSED: 100% of skills align perfectly`。

---

## 阶段二：灵魂大脑的语义级巡视 (Semantic Reasoning & Alignment)

物理探针通过后，说明系统已经守住了“不炸库、不写死路径”的生命线。现在，你需要释放你的 **大模型语义脑**，进行深度架构干预。

### 巡航规则：
在接下来的动作中，你不得敷衍了事，必须以**顶级架构师**的视角审视近期活跃的组件：

1. **调取近期活跃切片**：
   使用工具搜索 `openclaw/skills/` 下，最近被修改过、或是老板最近提到的 5 个核心技能 `SKILL.md`。
2. **反冗余与伪需求盘问 (Anti-Redundancy check)**：
   - 逐字阅读这 5 个技能的操作描述。
   - 它们之间有没有出现极其相似的“私造小轮子”？
   - 有没有把本可以用 `ls` 或 jq 解决的简单动作，硬写成了一大坨易碎的 Python 脚本？
3. **架构鲁棒性推演 (Resilience Stress Test)**：
   - 寻找这 5 个技能里描述的外部调用（如大模型调用、API 请求）。
   - 在你的脑海中模拟断网、无权限、或 API 超时。目前的 `SKILL.md` 指导流程里，是否缺乏足够的“被动防御”姿态和兜底手段？
4. **能力拓展延伸预判 (Expansion & Extrapolation)**：
   - 根据老板最近下达的科研任务（如跑 PhysDiff 或 CaLaM），这 5 个技能现有的能力边界是否足够？
   - 是否需要将某个特定动作抽象为一种全新的原子级 Skill？

### 阶段二交付物：
如果在推演中，你发现某个技能“在语义层面虽然没报错，但写得像一坨屎”或者“存在幻觉空间”，你**千万不要直接修改**。
你必须起草一份《系统语义层对齐建议修正案 (Implementation Plan)》，并使用 `notify_user` 阻塞进程，请求老板的审批。

---

> _"Under the 5th Law, we trust the code to stand the ground, and we trust the Agent to seek the truth."_
