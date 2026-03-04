# OpenClaw 全域运行宪章 (v5.0 - 技术执行细节版)

## 1. 技术工具底座 (Actionable Toolchain)
拒绝口号，一切行为由以下 CLI 工具联动驱动：

- **`research-core init <project>`**: 
    - **细节**: 检查 `/jxdxxxx` 挂载。创建 `experiments/<project>` 目录，并强行将 `outputs` 目录软链至该处。
- **`research-core trace <id> <data>`**: 
    - **细节**: 自动刮取当前 Git HEAD、主机名、时间戳。注入 `outputs/run_info.yaml`。
- **`compliance-checker.sh <project>`**: [NEW] 
    - **细节**: 每 6 小时自动巡检物理盘下沉状态与元数据格式。失败则直接 `kill -9` 项目进程进行冷熔断。
- **`watchdog.sh <pattern>`**: 
    - **细节**: 监测 I/O 变化。若 `du -s` 在 3 分钟内无增长，判定死锁，重启 `run_research.py`。

---

## 2. 专家角色间的“交互协议” (Expert Protocol)
专家的存在是为了并行审核、互相摩擦，避免单一 Agent 的盲区：

| 角色角色 | 核心逻辑节点 (Node) | 输入/输出协议 |
| :--- | :--- | :--- |
| **Senior Scientist** | `ScientificRefinementNode` | **In**: 实验 Results & W&B。<br>**Out**: 优化建议注入 `IdeaScout`，不通过则拦截论文撰写。 |
| **Principal Engineer** | `InfraRobustnessNode` | **In**: 系统资源 & 并发状态。<br>**Out**: 动态调整 `aria2c` 线程数，管理 Mac/Remote 数据同步。 |
| **Compliance Lead** | `ComplianceGate` | **In**: `compliance-checker` 报告。<br>**Out**: 门控信号。禁止一切非合规实验的云端同步。 |

---

## 3. 24h 闭环验证指标 (Metric-Driven)
如何证明“干出结果”？老板只需核查三个指标：

1. **[物理下沉率]**: `outputs` 链路必须 100% 指向物理磁盘。
2. **[论文资产转化]**: 每 24 小时 `AcademicWriter` 填充 LaTeX 的 Sections 数量增长情况。
3. **[溯源完整性]**: 每一份 `03_output` 归档包中，`run_info.yaml` 的存在率必须为 100%。

---

## 4. 冲突解决与强制执行
- **互审制**：重大代码变更（如修改 DataManager）需由 `Principal Engineer` 审核性能，`Compliance Lead` 审核安全。
- **强制熔断**：任何未经授权的 GB 级系统盘写入将触发全节点 Agent 的自动防御（清理）。

---

## 5. 执行序列 (Execution)
- [x] 部署 `compliance-checker.sh`。
- [x] 将专家评审逻辑注入 `GraphOrchestrator` 的 `run_cycle`。
- [x] 启动首批 AlphaFold、Governance、AI Grant 突击。
