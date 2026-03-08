---
name: sandbox-smith
description: L2 Meta-Skill for zero-download isolated venv generation and Hermetic Drop deployment.
---

# Sandbox Smith (沙盒司炉工)

> **核心使命 (Core Mission)**:
> 贯彻 L1 宪法之《沙盒囚禁法则》与《孤岛空投法则》。负责全自动生成 100% 断网隔离的 Python 运行结界，杜绝环境污染与依赖漂移。

## ⚙️ 战术动作 SOP (Tactical SOP)

面临新项目或重型组件需要本地或跨端隔离部署时，如果你准备动手拉撒环境，必须立刻调动 Sandbox Smith，严格按照以下铁血流程锻造环境：

### Phase 1: 防火墙物理建立 (The Firewall)
1. **立即拦截 Git 污染**: 在代码仓库落地的第一秒，强制写入并 `git add .gitignore`。
   - 必杀黑名单：`venv/`, `__pycache__/`, `*.whl`, `*.pt`, `*.onnx`, `*.safetensors`, `models/`。

### Phase 2: 真空打包提取 (The Hermetic Vacuum)
1. **纯净脱水提取**: 在拥有宽带出口的主节点 (如 Node 01) 执行绝对纯净剥离，不污染宿主全局：
   ```bash
   python3 -m pip download <heavy_libraries> -d /tmp/wheels_cache/ -i https://pypi.doubanio.com/simple/
   ```
2. **零配件跨端归档**: 收集完毕后，通过跨端 `scp` 强制将整个含有脱水二进制轮子的目录压缩包或 `.whl` 文件群，上载至冷冻冰库 **Node 03 (`~/openclaw_data/wheels_vault/`)** 进行永世封存。

### Phase 3: 沙盒自锁与结界成型 (The Incarceration)
1. 自动生成极简隔离安装脚本 (`install_isolation.sh`)，强制包含以下核心流水线：
   ```bash
   # 1. 斩断前因，创建纯净牢笼
   rm -rf venv && python3 -m venv venv
   # 2. 闭眼硬拼装 (杜绝一切网络获取，只听命于离线指令)
   ./venv/bin/pip install --no-index --find-links=/tmp/wheels_cache --no-deps <packages>
   ```
2. 在该技能或项目的 Python 主代码入口处，强制插加自杀式的“出圈探测锁”:
   ```python
   import sys, os
   in_venv = sys.prefix != sys.base_prefix
   if not in_venv:
       venv_python = os.path.join(os.path.dirname(os.path.abspath(__file__)), "venv/bin/python3")
       os.execv(venv_python, [venv_python] + sys.argv)
   ```

## ⚡ 触发条件 (TRIGGER RULE)
一旦你的脑海中浮现出 `pip install torch`, `pip install onnxruntime` 等试图将重型 C++ 张量框架或任何含复杂依赖的机器学习框架安装到当前系统的企图时，**绝对禁止裸奔执行**。必须立刻中断，调起本 `sandbox-smith` 技能法则，执行上述的三段式物理隔离装载流！
