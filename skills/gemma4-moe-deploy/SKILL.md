---
name: gemma4-moe-deploy
emoji: 🧬
description: Gemma 4 (128-Expert MoE) 跨架构微调与推理部署技能。涵盖 ms-swift 架构补丁注入、环境标准化、万兆直连权重同步及黄金训推指令集。源自 2026-04-05 生产实战。
---

# 🧬 Gemma 4 MoE 跨架构部署技能

## 背景
Gemma 4 (31B Dense / 26B-A4B MoE) 属于超新架构，发布时主流框架（ms-swift、vLLM）均未原生支持 128 专家 MoE。本技能记录了从零打通微调与推理的完整路径。

## 1. 核心铁律：统一环境底座

> [!IMPORTANT]
> **微调与推理统一使用 `conda activate swift`。**
> 该环境是目前集群中唯一同时闭环了 ms-swift MoE 补丁与 vLLM 推理引擎的全能底座。

| 任务 | Conda 环境 | 核心框架 | 关键版本锁 |
| :--- | :--- | :--- | :--- |
| **微调 (SFT)** | `swift` | `ms-swift` | `transformers==4.48.3` |
| **推理 (Inference)** | `swift` | `vLLM` | `vllm>=0.10.1` |

### 教训：环境冗余陷阱
- **禁止** 为每个模型创建独立 Conda 环境（如 `chic_vllm`、`gemma4`），这会导致 20-30GB 的存储浪费和版本碎片。
- 历史遗留的 `chic_vllm` (vLLM 0.6.1) 和 `gemma4` 环境已于 2026-04-05 彻底清理。

## 2. ms-swift 架构补丁注入 (Hyper-Compat Patch v1.6)

### 病因
ms-swift 未原生注册 `Gemma4ForConditionalGeneration` (128-Expert MoE)，直接运行 `swift sft` 会报 `ModelType not found`。

### 动作
需要修改 ms-swift 源码中的三个文件：

#### 2.1 注册模型常量
**文件**: `swift/llm/model/constant.py`
```python
# 在 LLMModelType 中注入
gemma4 = 'gemma4'
gemma4_moe = 'gemma4-moe'

# 在 MLLMModelType 中注入
gemma4 = 'gemma4'
```

#### 2.2 注册模型架构
**文件**: `swift/llm/model/model_arch.py`
```python
# 在 MLLMModelArch 中注入
gemma4 = 'gemma4'
```

#### 2.3 创建模型加载器
**文件**: `swift/llm/model/model/gemma4.py`

核心策略：使用 `AutoModel` 动态加载绕过 `transformers` 版本锁，让框架自动发现 128 专家 MoE 层。

```python
from transformers import AutoModelForCausalLM, AutoModel
# 使用 AutoModel.from_pretrained() 而非硬编码类名
# 这样即使 transformers 版本滞后，只要 config.json 中的
# architectures 字段包含 Gemma4ForConditionalGeneration，
# 框架就能正确实例化模型
```

### LoRA Target 映射
128 专家的 LoRA 目标层：
```
expert.*gate_proj, expert.*up_proj, expert.*down_proj
```

## 3. 跨架构权重同步：万兆直连协议

### 网络拓扑
```
GPU (10.190.30.220) ←→ ARM (10.190.31.33)
         ↕ 管理网 (200KB/s，禁止大文件)
GPU (18.18.1.1)     ←→ ARM (18.18.1.33)
         ↕ 万兆直连私网 (300-500MB/s，专用于权重同步)
```

> [!CAUTION]
> **本机 Mac 不在 18.18.1.x 子网内！**
> 从 Mac 发起的同步必须使用逻辑别名 `arm-34` 或管理网 IP，不能使用万兆私网 IP。
> 万兆直连仅限 GPU↔ARM 之间使用。

### 同步指令
```bash
# GPU → ARM（利用万兆直连，速率 300-500MB/s）
ssh gpu "rsync -avP /jhdx0003008/models/gemma-4-31b-it-nf4/ root@18.18.1.33:/data/workspace/models/gemma-4-31b-it-nf4/"

# Mac → ARM（走管理网，速率较低）
rsync -avP /local/path/ arm-34:/data/workspace/target/
```

### 教训：NFS 临时文件陷阱
- rsync 传输大文件时，目标端会生成 `.nfs*` 隐藏临时文件，普通 `ls` 看不到。
- 使用 `ls -la` 查看隐藏文件确认传输进度。
- 传输完成后务必执行 **MD5 双向校验**。

## 4. 黄金训练指令 (The Golden Command)

```bash
# Step 1: 激活环境
conda activate swift

# Step 2: 进入 ms-swift 源码目录
cd /jhdx0003008/code_zyf/ms-swift
export PYTHONPATH=$PYTHONPATH:.

# Step 3: 启动 SFT
swift sft \
  --model_type gemma4-moe \
  --model /jhdx0003008/models/gemma-4-26b-a4b-it-bnb-4bit \
  --dataset alpaca-zh \
  --num_train_epochs 1 \
  --batch_size 1 \
  --gradient_checkpointing true
```

## 5. 验收协议

环境交付前必须通过以下检查：
1. **补丁生效**: `swift sft --model_type gemma4-moe --help` 不报错
2. **LoRA 映射**: 训练日志中可见 `expert.*gate_proj` 层参与梯度更新
3. **推理验证**: `vllm serve` 能成功加载模型并响应请求
4. **MD5 一致**: GPU 与 ARM 侧的 `model.safetensors` MD5 完全匹配

## 6. 已知技术债务

| 项目 | 状态 | 影响 |
| :--- | :--- | :--- |
| `trl` 版本警告 | ⚠️ 可忽略 | 不影响核心 SFT 功能 |
| `vllm` 与 `transformers 4.48.3` 依赖冲突 | ⚠️ 可忽略 | 推理功能正常 |
| ARM 端 vLLM 对 128 专家的兼容性 | 🔴 待验证 | 需执行 mock inference 确认 |
