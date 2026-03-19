---
description: 如何设计论文对齐的实验矩阵（Experiment Matrix Design SOP）
---

# 实验矩阵设计 SOP

> **触发场景**: 当需要为一个研究项目设计或提交实验计划时
> **核心原则**: 实验矩阵由论文需求驱动，不是拍脑袋
> **铁律**: Step 0 就绪度检查是**自动触发**的，不需要 Boss 命令

---

## Step 0: 就绪度检查 ⚡ 自动触发，不等 Boss 问

> 在设计实验矩阵之前，必须先确认基础设施就绪。
> **这一步不需要 Boss 命令触发，是 Agent 的基本职责。**

```text
# 必须全部通过才能进入 Step 1
[ ] 环境:  conda env 可用？依赖齐全？
[ ] GPU:   几块？空闲状态？
[ ] 模型:  base model 权重在指定路径？
[ ] 辅助模型: risk_model / classifier 等已训练并就位？
[ ] 数据:  EXPERIMENT_MATRIX 里每个 dataset 的数据文件都存在？
[ ] W&B:   .netrc 认证？项目名对齐？
[ ] 断点续训: --resume / --start_index 已实现？
[ ] 日志:  PYTHONUNBUFFERED？tee 双写？
[ ] 代码:  所有待改代码已改完并 SCP 到 GPU？
[ ] GPU 隔离: 实验脚本有 --gpu 参数？(Law #5: Python 级 CVD, 不是 shell 级!)
```

**任何一项 ❌ → 先修再进 Step 1。**

---

## Step 1: 读论文结构（Top-Down）

列出论文的所有 Table / Figure / Claim：

```
Table 1: Main Results → 需要哪些方法对比行？
Table 2: Safety Bench → 需要哪些数据集？
Table 3: Ablation → 需要消融哪些组件？
Figure X: 敏感性分析 → 需要哪些参数变体？
```

每个 Table 的每一行 = 一个实验。

## Step 2: 读已有代码（Bottom-Up）

检查项目中是否已存在实验矩阵定义：

```bash
# 搜索已有的实验配置
grep -r "EXPERIMENT_MATRIX\|experiment_config\|CLAIM_TO" src/ config/
```

**已有的矩阵是第一优先参考**，不要绕过它自己编。

## Step 3: 覆盖性检查

对每个论文 Claim，验证是否有对应实验支撑：

```
Claim: "CaLaM outperforms DExperts"
  → 需要: calam_rtp_full + dexperts_rtp_full  ✅/❌？

Claim: "Geometry constraint is necessary"
  → 需要: calam_full + ablation_no_geom       ✅/❌？
```

**任何 Claim 没有对应实验 = 论文漏洞，必须补上。**

## Step 4: 分层执行

```
Phase A: Smoke Test（每实验 N=50，验证链路通畅）
  → 5 GPU 并行，~10 min 全部跑完
  → 目标: 无 crash、指标方向正确

Phase B: Production（论文标称数据量）
  → 按论文 Table 优先级排序
  → P0: Main Results（Table 1）
  → P1: Ablation（Table 3）— 审稿人必问
  → P2: Safety Bench（Table 2）
  → P3: Utility Retention
  → P4: 敏感性分析
```

## Step 5: 门控对齐

每个 Claim 对应一个数值门控：

```
Claim: "outperforms X" → our_metric < x_metric
Claim: "maintains utility" → our_utility > 90% * baseline
Claim: "ablation needed" → without_component > with_component
```

---

## 反面教材

```
❌ 拍脑袋: "跑 3 个实验应该够了"
❌ 闭眼干活: 不看 config.py 里已有的 EXPERIMENT_MATRIX
❌ 忽视消融: 只跑主实验不跑消融（审稿人第一个问）
❌ 忽视 Utility: 只报 safety 不报 utility（审稿人第二个问）
```

## Checklist（提交实验计划前必须过）

- [ ] 论文每个 Table/Figure 都有对应实验？
- [ ] 项目代码里已有的实验矩阵已查看？
- [ ] CLAIM_TO_EXPERIMENT_MAP 覆盖率 100%？
- [ ] Smoke 和 Production 分层？
- [ ] 每个 Claim 有数值门控？
- [ ] 消融实验完备（每个关键组件都有 w/o 版）？
- [ ] Utility 实验有对照组？
