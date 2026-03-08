---
name: skill-forge
description: The Meta-Skill factory for generating L1-compliant, Hermetic Drop AI skills.
---

# Skill Forge (AI 技能锻造局)

> **最高纲领 (Supreme Mandate)**:
> 凡涉及第三方复杂 C++ 库、深度学习张量框架 (如 Torch, ONNX, LLVM) 及数百兆模型的本地化 AI 技能开发，**必须且仅能**通过本兵工厂进行标准化一键生成。绝对禁止手工创建目录和裸敲 `pip install`。

## ⚔️ 自动化锻造流水线 (The Assembly Line)

### Phase 1: 防火墙预设与骨架生成 (Zero-Day Scaffold)
当你准备开发一个名为 `local-ocr` 或类似的大型技能时，只需执行：
```bash
python3 skills/skill-forge/scripts/forge.py --init local-ocr
```
**系统将为你全自动办砸三件事**：
1. **物理隔离**: 瞬间生成并定稿该技能目录的 `.gitignore`，天生防堵 `venv`, `*.whl`, `*.onnx` 级数据泄漏。
2. **基因锁死**: 自动生成的 Python 主体程序被注入“沙盒出圈即刻自毁”的高维探针代码。
3. **隔离部署管线**: 生成无需公网请求、仅靠底层文件句柄完成装配的 `install_isolation.sh`。

### Phase 2: 真空抽取轮子 (Hermetic Harvester)
在生成的 `requirements_core.txt` 中填入你需要的包名（例：`onnxruntime`, `paddleocr`）后执行：
```bash
python3 skills/skill-forge/scripts/forge.py --harvest local-ocr
```
**系统将为你全自动执行**：
1. 在具有透明网络底座的机器（Node 01\05）向外抽离所有纯二进制的 `.whl` 文件至物理抽屉 `/tmp/wheels_cache/<skill_name>`。
2. 自动将其高压封合为 `<skill_name>_wheels.zip` 重资产包。
3. 一脚通过 `scp` 踹入冰冷的地宫：`Node 03 (~/openclaw_data/wheels_vault/)` 永恒保存。

### Phase 3: 群星轨道伞降 (Orbital Drop Deployment)
当代码已开发完成并 Git Push，此时想将技能实装到 Node 02/03：
```bash
# 此阶段正在与全局 ssh_tool.py 并网中，目前手动遵循：
1. Target Node 必须使用 git pull 收取主控代码。
2. Target Node 必须使用 scp 03:... 拉取冰库重资产。
3. 运行该技能目录下的 ./install_isolation.sh 完成最后组装缝合。
```

---

## ⚡ 触发条件 (TRIGGER RULE)
**何时拔出此剑？**
当收到老板下达：“开发/迁移 XXX 服务到本地”、“做个离线的 XXX 功能”、“部署 XXX 预研环境”。
**只要需求中包含安装大量的外部开源 AI 库，本工具的唤醒优先级绝对置顶！绝对禁止手工创建。**
