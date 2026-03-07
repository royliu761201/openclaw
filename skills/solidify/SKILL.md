---
name: solidify
description: The ultimate cognitive immune system. Use this skill to physically inject retrospectives, anti-patterns, and bug fixes into the agent's absolute genetic memory (L1 Constitution, L2 Skills, or L3 Antibodies).
metadata: { "openclaw": { "emoji": "💉", "requires": { "bins": [] } } }
---

# Cognitive Solidification (基因锚定与抗体注射)

## Objective

In OpenClaw, "talking about a lesson" is invalid. Lessons, bug fixes, user corrections, and process improvements MUST be physically encoded into the workspace documents so that future agents are immune to the same mistakes. 

The `solidify` skill represents the "A" (Act - 固化) in the PDCA cycle. Agents **MUST** use this protocol whenever a problem is resolved or a workflow is optimized.

## Trigger

Whenever you successfully complete a debug loop, receive a strict correction from the boss, or propose a PDCA reflection, you MUST engage this skill to physically write the rule down. **Do NOT just say "I have learned."** You must execute the injection.

## Execution Rules (The 3-Tier Injection Protocol)

When solidifying a lesson, the Agent must use `replace_file_content` to append the rule into ONE of the following three Tiers based on its scope:

### 1. `[L1]` 全局宪法 (The Boot Gene)
* **Target File**: `/Users/roy-jd/workspace/docs/system_core/GEMINI_L1_CONSTITUTION.md`
* **Trigger Condition**: Use this ONLY for absolute, life-or-death, universal agent rules (e.g., "Never rm -rf", "Always Output Plan First").
* **Action**: Append the rule to the "老板核心铁律" section.

### 2. `[L2]` 专科抗体 (Skill Guardrails)
* **Target File**: `/Users/roy-jd/Documents/projects/openclaw/skills/<relevant-skill>/SKILL.md`
* **Trigger Condition**: Use this for tool-specific bugs, missing parameters, or usage quirks (e.g., "Paramiko drops connection due to SSH_PORT").
* **Action**: Append a `### 🚫 防坑禁区 (Anti-Hallucination)` section at the bottom of the tool's `SKILL.md`.

### 3. `[L3]` 微观免疫库 (Agent Antibodies Vault)
* **Target File**: `/Users/roy-jd/workspace/docs/system_core/AGENT_ANTIBODIES.md`
* **Trigger Condition**: Use this for bad agentic habits, workflow inefficiencies, and general command-line behavioral corrections (e.g., "Agent shouldn't use bash to parse JSON, use jq").
* **Action**: Append the anti-pattern using the `[AB-XXX]` dictionary format.

## Conclusion

Once the file is successfully altered via `replace_file_content`, inform the boss with exact precision:
>"已触发 `solidify` 技能。已将 [Your Observation] 作为免疫抗体注入 [L1/L2/L3 File Path]。绝不再犯。"
