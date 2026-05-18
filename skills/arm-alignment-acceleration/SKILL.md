---
name: arm-alignment-acceleration
description: 针对异构 ARM 集群 (如 L20 节点) 执行环境跨架构转移、极速构建及规避 NFS I/O 阻塞的专项抢险技能库。V3.0 新增万兆直连私网协议、Conda 环境生命周期管理及 Gemma 4 MoE 兼容性指引。
---

# ARM 集群环境极速对齐指引 (V3.0)

在 ARM (Aarch64) L20 集群上，传统的 `conda create` 流程极易产生二进制碎片与算子断裂。本技能确立了 **"单点饱和注入，全集群物理克隆"** 的最高对齐协议。

## 1. 核心铁律：政策 1:1 对齐 (Article 11 Inheritance)
### 场景与病因
若 ARM 节点网络环境不通，会导致实验回传 (WandB) 或模型下载 (HuggingFace) 阻塞，形成"环境孤岛"。
### 动作 (The Mandate)
- **镜像劫持**：必须将 `~/.pip/pip.conf` 强制指向 Aliyun 镜像。
- **HF 劫持**：必须在 `.bashrc` 注入 `export HF_ENDPOINT=https://hf-mirror.com`。
- **共识**：ARM 节点即是 "ARM 版的 GPU 服务器"，继承 Article 1 的所有网络白名单。

## 2. 物理层空间隔离：物理位图复刻法 (The Rsync Mandate)
### 场景与病因
异构集群安装依赖时，由于 ARM 的复杂依赖树，`conda` 解析常因 IO 阻塞或网络波动导致安装不完整（如 Pytorch3D 缺算子）。
### 动作 (The Mandate)
- **黄金母盘先行**：优先在 `frenet` 环境中完成 100% 算子调优（Pytorch3D, SAM2 等）。
- **物理复刻**：严禁在其他环境重复安装！使用 `rsync -a` 从母盘物理克隆整个 Conda 目录。
- **效率**：比 `conda create` 提速 400%，且物理保证二进制 100% 相同。

## 3. 逻辑层路径锚定：Shebang 原子修正 (Path Anchor)
### 场景与病因
物理复刻后的 Conda 环境会因为父文件夹变动（如从 `/frenet` 到 `/pesso`），导致 `bin/` 下的解释器路径（Shebang）失效，包无法调用。
### 动作 (The Mandate)
克隆后必须立即执行 `sed` 原子修正：
```bash
# 修正示例
sed -i '1s|/frenet/bin/python|/pesso/bin/python|' /new/env/bin/*
```

## 4. 算力层硬核对齐：sm_90a 编译强制令
### 场景与病因
ARM 节点的 Ninja 编译器常因内核版本产生架构幻觉，导致编译出的算子不支持 L20。
### 动作 (The Mandate)
任何 CUDA 扩展编译前，**必须执行环境变量锁死**：
```bash
export TORCH_CUDA_ARCH_LIST="9.0"
export CUDA_HOME=/usr/local/cuda-12.4
```

## 5. 验收铁律：三位一标验收 (Verification Protocol)
**环境交付前，必须执行全栈压力探测：**
1. **CUDA 探测**：`torch.cuda.is_available() == True`。
2. **算子探测**：`import pytorch3d.ops` 无动态库报错。
3. **外联探测**：`curl -I https://api.wandb.ai` 联运就绪。

---

## 6. 【V3.0 新增】万兆直连私网协议 (10GbE Direct-Link Protocol)

> [!IMPORTANT]
> 本节源自 2026-04-05 Gemma 4 跨架构部署实战。

### 6.1 网络拓扑与使用规则
```
管理网 (低速，200KB/s)：
  Mac ↔ GPU (ssh gpu)   ↔ ARM (ssh arm-34)

万兆直连私网 (高速，300-500MB/s)：
  GPU (18.18.1.1)  ↔  ARM (18.18.1.32 -p 30449)
  GPU (18.18.1.1)  ↔  ARM (18.18.1.33 -p 32404)
  ⚠️ 仅限 GPU↔ARM 之间！Mac 无法直接访问！
```

### 6.2 大文件同步必须走万兆直连
```bash
# ✅ 正确：GPU→ARM 通过万兆直连同步模型权重
ssh gpu "rsync -avP -e 'ssh -p 32404' /jhdx0003008/models/MODEL_DIR/ root@18.18.1.33:/data/workspace/models/MODEL_DIR/"

# ❌ 错误：从 Mac 直连万兆私网 IP（会被拒绝）
rsync -avP ./model arm-34@18.18.1.33:/data/workspace/  # Connection refused!

# ✅ 正确：从 Mac 同步需用逻辑别名
rsync -avP ./model arm-34:/data/workspace/
```

### 6.3 教训：NFS 临时文件与 MD5 校验
- rsync 传输大文件（>1GB）时，目标端会生成 `.nfs*` 隐藏临时句柄。
- 使用 `ls -la` 而非 `ls -lh` 查看实际传输进度。
- **传输完成后必须执行 MD5 双向校验**：
```bash
ssh gpu "md5sum /jhdx0003008/models/MODEL/file.safetensors"
ssh arm-34 "md5sum /data/workspace/models/MODEL/file.safetensors"
# 两个哈希值必须完全一致！
```

## 7. 【V3.0 新增】Conda 环境生命周期管理 (Env Lifecycle)

> [!CAUTION]
> 集群中曾因"每模型一环境"策略积累了 27GB+ 冗余环境（`chic_vllm`、`gemma4` 等），严重侵蚀 1.1P 共享存储。

### 7.1 环境创建原则
- **禁止** 为单个模型创建独立 Conda 环境。
- **优先** 在现有环境（如 `swift`、`base-research`）中通过 `pip install` 增量安装。
- 仅当存在 **不可调和的依赖冲突** 时，方可创建新环境。

### 7.2 定期清理协议
每季度执行一次环境审计：
```bash
# 列出所有环境及占用空间
conda env list
du -sh /root/miniconda3/envs/*/

# 检查是否有活跃进程
ps -ef | grep python

# 清理确认无用的环境
conda env remove -n ENV_NAME -y
```

### 7.3 ARM 侧环境路径规范
ARM 节点没有 `/root/miniconda3/`，环境统一存放在：
```
/data/workspace/envs/aarch64/[环境名]/
```
激活方式：
```bash
source /data/workspace/envs/aarch64/[环境名]/bin/activate
```

**严格执行此闭环后，方可宣布 ARM 节点具备 NeurIPS 2026 生产力。**
