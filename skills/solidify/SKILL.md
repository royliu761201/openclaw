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

## 🧭 L0-L3 REFLECTION PROTOCOL (The Dissection Knife)

Every retrospective output MUST strictly adhere to the structural breakdown of the L0-L3 framework. You are forbidden from generating generic, unstructured diaries. You must explicitly evaluate and document:

- **[L0 Survival Baseline]**: Did this failure breach physical sandbox safety, leave zombie daemons (e.g., Nohup ghosts), or violate network firewalls/SSH pipelines?
- **[L1 Workspace SSoT]**: Did this failure stem from data hallucination (Mocking data instead of using physical HDF5/Truth files), Git-as-Bus flow violations, or failing to probe environment variables?
- **[L2 Meta-Skills]**: Was this failure caused by performing repetitive tasks manually instead of utilizing or building an automated capability, probe, or cron job?
- **[L3 Domain Mastery]**: What are the specific model, pipeline, or physical metrics outcomes and remaining architectural bottlenecks?

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
- Or, if it is a global constitutional law, append it directly to `~/workspace/.clinerules`.

### 4. Payload / Context Hydration (The Final Lock)

If your reflection concludes that a specific system-level tool or script (like `skill-aligner` or `net-probe`) must be habitually accessible moving forward, it is **YOUR RESPONSIBILITY** to ensure it is physically mounted in the Agent's context.

- Execute a shell command to symlink the tool into the active payload: `ln -sf ~/openclaw/skills/<skill-name> ~/.local_skills/<skill-name>`.
- Without this physical mounting, your textual constitutional updates are useless, as subsequent Agents will not be equipped to follow them.

## 🩸 THE BLOOD LAW (Mandatory Execution Tie-in)

**A retrospective must NEVER end with "I will pay attention next time."**
At the conclusion of your reflection document, you MUST append a **[🔥 Action Plan (物理实装行动计划)]**.
Following the generation of the retrospective artifact, you are **MANDATED** to remain in the active task and immediately switch to `EXECUTION` mode to write the corresponding script, daemon, or assertion code (e.g., `pkill-first` bash wrappers, or Git automation scripts) that physically fixes the identified gap. If you fail to write the physical code after a retrospective, your solidification process is deemed incomplete and fraudulent.

## 🪞 THE PROJECTION BIND

Upon generating and saving the retrospective artifact to the `brain` directory, you MUST actively invoke the UI projection mechanism (`notify_user` with `PathsToReview`) to present the formulated text to the Boss. Silent caching is strictly forbidden.

## ⚠️ CONSTITUTIONAL ANCHORS

- **The Reflex Law**: Never report a task as "Done" if you admitted a mistake during execution, UNLESS you have executed the `solidify` skill to record the antibody.
- **English-Only Directives**: When writing internal logic for skills (`SKILL.md`) or system rules (`.clinerules`), you MUST write in pure English to prevent logical prompt drifting.
