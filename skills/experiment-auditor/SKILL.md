---
name: experiment-auditor
emoji: 🔬
description: >
  强制实验审计技能。在每个实验结束后执行 W&B 指标核查、日志污染检测、
  论文数字来源验证。是「14_SCIENTIFIC_CLAIM_LAW」和「13_EXPERIMENT_AUDIT_LAW」的可执行实现。
  任何实验在 W&B 门控未通过前，禁止在 PDCA 打 [x]。
metadata:
  openclaw:
    requires:
      bins: ["python3"]
      skills: ["wandb"]
---

# 🔬 Experiment Auditor 技能

将 `13_EXPERIMENT_AUDIT_LAW.md` 和 `14_SCIENTIFIC_CLAIM_LAW.md` 中的制度条款**变成可执行代码**。

## 核心工具

### `post_experiment_gate` — 实验终点必经关口

**在每个实验脚本末尾调用。通过才能打 [x]，失败必须修复。**

```bash
python workspace/scripts/post_experiment_gate.py \
    --project calam \
    --run_id <W&B Run ID> \
    --log calam_eval.log

# 返回 0 = 通过，可打 [x]
# 返回 1 = 失败，禁止打 [x]
```

**三项核查逻辑**：

1. **W&B Gate**：Run 的 Summary 中必须包含项目规定的所有指标 key（如 `j_score_pct`、`pb_valid_rate`）且值不为 `-1`
2. **Log Gate**：日志中无 `Dummy/Fallback/scaffold/MockModel/--mock` 等污染关键词
3. **Score Gate**：关键指标不是降级值（toxicity=-1 等）

### `recover_experiment.py` — 灾后恢复一键装甲 (15_LAW)

**当实验崩溃时调用。自动清理 W&B 云端污染，并通过 SSH 远程抹除 GPU 的僵尸日志。**

```bash
python workspace/scripts/recover_experiment.py \
    --project calam \
    --remote_host gpu \
    --remote_path /jhdx0003008/workspace/projects_core/CaLaM

# 集成逻辑：
# 1. 连接 W&B API，物理硬删所有状态为 failed/crashed 的条目。
# 2. SSH 远程执行 find -delete 扫除所有的 smoke_*.log 与 .lock 死锁残留。
# 3. 探明残留进程供 Agent 进一步执行 kill -9 释放 VRAM。
```

---

## 🔬 Physics & Memory Disaster Triage (PDE Math & OOM Profiling)

当实验没有通过 `post_experiment_gate`，且在远端呈现**硬性崩溃**而非收敛极差时，必须执行以下物理免疫排雷与重构原则：

### 1. PDE Stability Triggers (`NaN` 激波溢出判定)

- **触发条件**：模型在 Epoch 0 或 Step 0 稳定报出 `NaN` 的 Loss。
- **强制阻断**：绝不可通过单纯降低 Learning Rate 来妥协。对于如 Burgers 等产生尖锐激波的物理场方程，原生的谱方法 (`spectral`) 物理核或极窄尺度的差分核心会在遇到非连续激波时遭遇 **CFL 条件崩溃**。
- **强制回退机制**：立刻修改实验的超参，强行注入并激活后备的 `upwind` 迎风有限差分算子。它是牺牲精度换取绝对稳定性的兜底架构。

### 2. Silent OOM Triage (幽灵崩溃追踪)

- **触发条件**：没有任何 `Python traceback` 报错，终端仅留下被 `OOM-Killer` 或系统守护进程强制终止的日志（可能表现出毫无征兆的休眠或突然的 255 退出）。
- **强制阻断**：立刻禁止使用推测执行机制或任何前置依赖编译器优化的框架组合。
- **调查流程**：
  1. 使用绝对独立的 Unbuffered (无缓冲) 探针重启实验：`python -u scripts/main.py` 以暴露被挂起的真实调用。
  2. 强制注释剥离所有的 `torch.compile` 包裹。在多层网络融合时，Triton 动态图会由于特征抽取阶段的微小分支，指数级膨胀编译期的 GPU VRAM 开销。
  3. 执行微小 `batch_size` 测试，证明原生 PyTorch 流水线没有逻辑故障。

### 3. TypeError Runtime Evasion (Dynamic Typing Triage)

- **触发条件**：Python 脚本在运行数分钟甚至数十分钟且加载完百 GB 模型权重后，由于深层调用链缺失必填参数（例如 `next_token_logits` API 签名变更）而引发 `TypeError` 突然死亡。
- **Fail-Fast 强制阻断**：严禁无保护地直接进入真实的百万数据大循环！
- **架构硬性规定（Dummy Forward Pass 毒性测试）**：
  在主要网络和损失函数实例化完毕，真正开始加载大型数据集**之前**，强制构造一个极小维度的全 0 伪造 Batch（`torch.zeros`），将这个 Dummy Input 穿透一次完整的 `model(dummy) -> loss.backward()` 流程。
  如果代码的 API 签名存在错位拼写或丢失传参，它必定在**最开头的一秒钟当场暴毙**，从而实现完美的 Fail-Fast 拦截，保护昂贵的显存和时间。

---

## 项目指标配置表（在 `post_experiment_gate.py` 中维护）

| 项目       | 必须出现在 W&B Summary 中                      |
| ---------- | ---------------------------------------------- |
| `calam`    | `j_score_pct`, `avg_toxicity`, `n_evaluated`   |
| `physdiff` | `pb_valid_rate`, `clash_score`, `rmsd`         |
| `frenet`   | `gap_closure_rate`, `dice_score`, `n_patients` |
| `pesso`    | `val_loss`, `stable_horizon`, `dataset_size`   |

---

## 集成方法（如何把门控嵌入实验管线）

### 方法 A：在 Python 脚本末尾显式调用

```python
# main.py 末尾
import subprocess, sys
result = subprocess.run([
    sys.executable, "workspace/scripts/post_experiment_gate.py",
    "--project", "calam",
    "--run_id", wandb.run.id,
    "--log", "calam_eval.log"
])
if result.returncode != 0:
    sys.exit(1)   # 实验未通过审计，不打勾
```

### 方法 B：在 shell 脚本末尾调用

```bash
# start_calam.sh 末尾
python workspace/scripts/post_experiment_gate.py \
    --project calam \
    --run_id "$WANDB_RUN_ID" \
    --log calam_eval.log
[ $? -eq 0 ] && echo "✅ 审计通过，可以打 [x]" || echo "❌ 审计失败，禁止打 [x]"
```

---

## 与其他技能的关系

| 依赖技能        | 用途                                           |
| --------------- | ---------------------------------------------- |
| `wandb`         | 读取 Run Summary，核查指标 key 是否存在        |
| `paper-crafter` | 在写论文前 lint LaTeX，检查 hardcoded 数字泄漏 |
| `workspace`     | 读取日志文件进行污染检测                       |
