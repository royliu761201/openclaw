# OpenClaw 数据集与实验数据规范 (OpenClaw Data & Exp Standard)

> [!IMPORTANT]
> 本文件为 OpenClaw 体系内数据集管理与实验数据记录的“基本法”。所有 Agent 及开发者必须严格遵守。

## 1. 存储原则：硬存软链 (Hard Storage, Soft Link)

- **物理下沉**: 所有 GB 级数据（数据集、权重、大型实验产出）物理存放在 `/jxdxxxx/openclaw_data` (GPU服务) 或 `~/openclaw_data` (Mac 03)。
- **逻辑映射**: `/root` 或项目目录内的 `01_input/`, `03_output/` 严禁存放物理大文件，必须使用 `ln -s` 指向物理存储路径。
- **系统盘保护**: 严控 `/root` 空间，违者审计失效。

## 2. 数据集规范：三层五段制

- **三层结构**: `raw/` (原始), `processed/` (预处理), `weights/` (权重)。
- **五段命名**: `<Source>_<Name>_<Config>_<Split>_<Version>` (例: `hf_llama3_8b_instruct_v1`)。
- **金库制度**: Mac 03 (roy-003) 永久保留所有 `raw/` 数据的备份。

## 3. 实验数据规范：全周期闭环

- **结构化产出**: 每个实验必须产出 `logs/`, `checkpoints/` (仅限 best/last), `visuals/`, `metrics.json`。
- **溯源强制**: 实验目录必须包含 `run_info.yaml`，记录 `Git_Commit_ID` 和 `Dataset_ID`。

## 4. 工具链

- **并发下载**: 强制使用 `aria2c` (16线程) 发起拉取。
- **一致性校验**: 使用 `rsync --checksum` 对齐计算节点与金库数据。
