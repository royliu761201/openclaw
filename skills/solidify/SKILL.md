---
name: solidify
description: The cognitive immune system of Antigravity. Executes the "Reflex Law" to permanently inject lessons learned, bug fixes, and architectural truths into the local/global SSoT (Ontology, L1 Constitution, or L2 Skills).
---

# `solidify` Skill

The `solidify` skill is the core execution mechanism for the ["Act" phase of the PDCA loop](../../docs/system_core/GEMINI_L1_CONSTITUTION.md). It ensures the Agent never repeats a mistake.

## ⚡️ TRIGGER RULES

You MUST execute this skill silently (without waiting for Boss's permission) when:

- You discover a system bug and resolve it.
- You output phrases like "Lesson learned", "Reflection", "反思", or "I realized".
- You uncover a new architectural truth or restriction about the OpenClaw grid or local workspace environments.

## 🛠️ USAGE (Pure MD-Driven SOP)

The solidification process must be routed based on the scope of the new knowledge.

### 1. Skill-Level Antibody Injection (L2)

If the finding is related to a specific operational skill (e.g., `ssh` failing due to env vars, or `git` hanging due to headless auth):

- Use `view_file` to read the target `SKILL.md`.
- Use `multi_replace_file_content` to inject the new rule into the `[Anti-Hallucination]` section of that specific `SKILL.md`.

### 2. Workspace / Project-Level Laws (L1 Local)

If the finding dictates how a specific project (e.g., a paper repository) must be handled (e.g., "Do not commit .safetensors"):

- Inject the rule into the `~/workspace/.clinerules` file or the specific project's local `.clinerules` file.

### 3. Global Architecture / Ontology Injection (L3)

If the finding is a universal truth about the physical environment (e.g., Node IP changes, OpenClaw schema strictness):

- Update the Knowledge Graph by appending a JSONL row to `~/workspace/docs/system_core/memory_core/ontology/graph.jsonl`.
- Or, if it is a global constitutional law, append it to `~/workspace/docs/system_core/GEMINI_L1_CONSTITUTION.md` (via its soft link if applicable).

## ⚠️ CONSTITUTIONAL ANCHORS

- **The Reflex Law**: Never report a task as "Done" if you admitted a mistake during execution, UNLESS you have executed the `solidify` skill to record the antibody.
- **English-Only Directives**: When writing internal logic for skills (`SKILL.md`) or system rules (`.clinerules`), you MUST write in pure English to prevent logical prompt drifting.
