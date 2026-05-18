---
name: whitebox-analysis
description: Mandatory SOP for performing deep whitebox source code analysis on any project. Enforces the "Call-Chain Driven" protocol: map first, grep to locate, view_file to read exact lines, follow call chains. Forbids web-search-based summarization as a substitute for actual code reading.
---

# `whitebox-analysis` Skill

## ⚡️ TRIGGER RULES

You MUST execute this skill when:
- The Boss says "白盒分析", "源码分析", "code walkthrough", or "whitebox".
- You are asked to explain HOW a system works internally (not WHAT it does).
- You are debugging an issue that requires tracing the actual execution path.

> **[Anti-Hallucination Guard]**: You are STRICTLY FORBIDDEN from producing a
> "whitebox analysis" report that is based on web search results, documentation,
> or prior knowledge alone. If you cannot get the actual source code, you MUST
> explicitly tell the Boss: "I do not have local access to the source code. The
> following is a structural overview only, NOT a whitebox analysis."

---

## 🗺️ PHASE 1: MAP FIRST (Architecture Recon)

Before reading a single source file, you MUST build a mental map.

```bash
# 1. Understand scale
find <project_root> -type f -name "*.py" | wc -l

# 2. Understand directory structure (max 2 levels deep)
ls <project_root>/
ls <project_root>/<main_package>/

# 3. Confirm the true entry point (never assume)
grep -rn "class <MainClass>" <project_root>/
```

**Do NOT skip this phase.** Without a map, all subsequent reading is directionless.

---

## 🔗 PHASE 2: CALL-CHAIN DRIVEN DESCENT

Start from the confirmed entry point and follow the call chain **one hop at a time**.

### The "One Hop" Rule

Each step in the analysis must follow this pattern:

1. **Read the current function** using `view_file` with precise line ranges (not the whole file).
2. **Identify the next call** — a method call, class instantiation, or IPC boundary.
3. **Locate it** using `grep`.
4. **Repeat**.

```bash
# Example descent for vLLM:
# Hop 1: Confirm LLMEngine is the entry
grep -n "class LLMEngine" vllm/engine/llm_engine.py

# Hop 2: Read __init__ and identify the next delegation
view_file vllm/v1/engine/llm_engine.py (L1-100)

# Hop 3: Follow the delegation (engine_core = EngineCoreClient.make_client(...))
grep -rn "class EngineCoreClient" vllm/
view_file <found_file> (relevant lines)

# ... continue until you reach GPU execution
```

### Call Chain Documentation Template

As you descend, document each hop:

```
LLMEngine.step()                  [vllm/v1/engine/llm_engine.py:L142]
  → engine_core.get_output()      [vllm/v1/engine/core_client.py:L??]
    → EngineCore.__run_loop()     [vllm/v1/engine/core.py:L??]
      → scheduler.schedule()      [vllm/v1/core/sched/scheduler.py:L??]
        → kv_cache_manager.allocate_slots()  [vllm/v1/core/kv_cache_manager.py:L??]
```

---

## 🔍 PHASE 3: HORIZONTAL CROSS-SECTION (Who-Calls-What)

After descending the primary call chain, perform horizontal grep sweeps to understand
the full reference graph.

```bash
# Find all callers of a function
grep -rn "allocate_slots(" vllm/

# Find all subclasses of a base class
grep -rn "class.*Scheduler" vllm/

# Find all places a config field is read
grep -rn "max_num_seqs" vllm/
```

This phase answers: **"Where else in the system does this matter?"**

---

## ✅ PHASE 4: HYPOTHESIS VALIDATION

Before writing any conclusion, form a hypothesis and immediately verify it in code.

| Hypothesis | How to Verify |
|---|---|
| "Preemption is triggered by a separate function" | `grep -n "def preempt\|evict" scheduler.py` |
| "Requests are stored in a priority queue" | `grep -n "class.*Queue\|heapq\|deque" scheduler.py` |
| "KV cache uses contiguous memory" | `grep -n "torch.empty\|contiguous" cache_engine.py` |

**If the code contradicts your hypothesis, the code wins. Always.**

---

## 📦 LOGISTICS PROTOCOL: Getting the Code

Follow this priority order:

1. **Local clone is already present**: Use `find` + `grep_search` + `view_file` directly.
2. **Network available (China)**: Use Node 05 as SOCKS5 proxy:
   ```bash
   ssh -D 1080 -f -C -q -N 05
   HTTPS_PROXY=socks5://127.0.0.1:1080 git clone --depth 1 <repo_url>
   ```
3. **Surgical fetch of key files** (when clone is impossible): Use `read_url_content` + `view_content_chunk`
   on raw GitHub URLs. But document ALL fetched files explicitly so the analysis is reproducible.
4. **Cannot get code**: Declare "structural overview only" — see Anti-Hallucination Guard above.

> **[AB-023 Warning]**: Do NOT use Paramiko-based tools (`ssh_tool.py upload`) to
> transfer large archives over Tailscale (100.x.x.x). Use native `rsync` instead.
> Windows nodes (05) do not have `rsync` — use `git clone --depth 1` directly on 05
> via SSH, then `scp` small zip archives, or establish a SOCKS5 tunnel back to Mac.

---

## 📋 OUTPUT FORMAT

The final whitebox analysis artifact MUST include:

1. **Call Chain Map** (numbered hop-by-hop, with file:line references)
2. **Annotated Code Snippets** (real code, not paraphrases)
3. **Horizontal Cross-Section Findings** (who-calls-what grep results)
4. **Hypothesis vs. Reality Table** (what you expected vs. what the code shows)
5. **Data Flow Diagram** (ASCII or mermaid)

---

## ⚠️ CONSTITUTIONAL ANCHORS

- **The Code Supremacy Law**: Source code is the only ground truth. Documentation, READMEs, and web articles are secondary references that must be verified against code.
- **The No-Substitute Law**: You CANNOT substitute a web-search summary for actual source code reading and call it a "whitebox analysis". This constitutes cognitive fraud.
- **The Map-First Law**: You are forbidden from reading any source file before surveying the directory structure and confirming the entry point via grep.
