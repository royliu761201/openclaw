---
name: vram-queue-manager
description: A mandatory task dispatcher skill that prevents GPU OOM crashes by polling `nvidia-smi` to ensure sufficient VRAM is available before launching multi-node Deep Learning jobs. Oviates the need for dangerous `nohup ... &` background flooding.
---

# VRAM Queue Manager Skill

## Overview
When an OpenClaw Agent is tasked with running a "Parameter Sweep", "Multiple Baselines", or "Evaluation Matrix", using raw parallel bash commands (`nohup CMD &`) easily causes VRAM collisions (Out Of Memory) when multiple models land on the same GPU simultaneously.

This skill provides a Python-based queue manager (`scripts/vram_scheduler.py`) that strictly polls GPU free memory and dynamically launches processes from a JSON task list only when the hardware is ready.

## Engineering Protocol (How to use)

### 1. Create a `tasks.json` file
Define exactly what the shell operations are.
```json
[
  {
    "name": "Burgers_1D_PESSO",
    "cmd": "source /root/miniconda3/etc/profile.d/conda.sh && conda activate pesso && python scripts/train_pesso.py --task burgers --model pesso",
    "env": {"CUDA_VISIBLE_DEVICES": "0"}
  },
  {
    "name": "Burgers_1D_FNO",
    "cmd": "source /root/miniconda3/etc/profile.d/conda.sh && conda activate pesso && python scripts/train_pesso.py --task burgers --model fno",
    "env": {"CUDA_VISIBLE_DEVICES": "1"}
  }
]
```

### 2. Launch the Scheduler
Use the `vram_scheduler.py` script and pass the minimum required VRAM per job (in GB).

```bash
python /Users/roy-jd/openclaw/skills/vram-queue-manager/scripts/vram_scheduler.py \
    --tasks tasks.json \
    --min-vram-gb 18 \
    --poll-interval 15
```

### 3. Agent Rules
- **DO NOT** use this locally on your Mac (`mps`) unless explicitly authorized. This is designed to be injected into `ssh` payloads or launched on remote GPU nodes (like `gpu` 0, 1 or `90-1`).
- By utilizing this framework, you comply with `14_SCIENCE_FIRST_LAW.md` regarding dispatch safety.
