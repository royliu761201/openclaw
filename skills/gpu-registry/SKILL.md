---
name: gpu-registry
emoji: 🗃️
description: Formalize compute allocation and lock GPU resources in the global SSoT registry.
metadata: { "openclaw": { "requires": { "bins": ["python3"] } } }
---

# GPU Registry & Allocation Skill

This skill enforces strict SSoT rules across the entire GPU cluster. Any AI agent or developer requiring computational resources must interact with this skill to lock/free cards to prevent race conditions and "OOM collisions" between parallel multi-agent runs.

## 核心法则 (Core Directives)

> [!IMPORTANT]
> **No Ghosting (拒绝幽灵占用)**
> You MUST NOT write ad-hoc markdown parsing scripts every time you need a GPU. Use the `gpu_allocator.py` script provided here to manipulate `08_GLOBAL_GPU_REGISTRY.md` reliably.
> Do NOT launch background jobs unless the GPU is formally marked `🔴 RUNNING` in the registry and the allocated GPU ID is returned.

## 工具清单 (Tools)

### 1. `allocate` (申请空闲算力)

Search for an available `🟢 FREE` GPU and lock it with your project/task name.

```bash
python3 /Users/roy-jd/openclaw/skills/gpu-registry/scripts/gpu_allocator.py allocate --node "gpu" --project "MyProject" --task "MyTask" --assigned "MyAgent"
```

If successful, the script will output exactly which GPU ID was locked.

### 2. `free` (释放算力)

Return your completed task's GPU to the available pool.

```bash
python3 /Users/roy-jd/openclaw/skills/gpu-registry/scripts/gpu_allocator.py free --node "gpu" --gpu_id "GPU-0"
```

### 3. `status` (当前全局算力快照)

Read a quick digest of currently running tasks and free slots across the cluster.

```bash
python3 /Users/roy-jd/openclaw/skills/gpu-registry/scripts/gpu_allocator.py status
```
