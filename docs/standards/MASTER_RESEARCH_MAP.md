# OpenClaw 独立科学审计规范 (Scientific Integrity)

## 1. 审计底线 (Audit Bottom Lines)
- **[数据真实性]**: 严禁通过代码注入假 Loss 或伪造测试结果。
- **[溯源完整性]**: `run_info.yaml` 必须包含物理盘下沉路径，否则审计结果为 `FAIL`。
- **[逻辑闭环]**: 实验产出必须经过 `Senior Scientist` 节点的有效性交叉验证。

## 2. 自动化审计工具 (`scientific_auditor.sh`)
- 检查 `outputs/` 下是否包含异常的随机数分布（预防测试造假）。
- 检查 `LaTeX` 段落中提及的指标是否能与 `metrics.json` 物理对应。

## 3. 分级处理
- **PASS**: 允许进入 `vault-sync` 与 `Paper-Archive`。
- **FAIL**: 立即执行 `pkill`，删除该轮垃圾数据。
