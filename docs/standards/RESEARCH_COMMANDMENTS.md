# OpenClaw 科研团队核心宪章 (The Research Commandments)

> [!IMPORTANT]
> **24小时无间断准则**：科研不穿机，活计不停歇。Agent 必须具备全天诊疗、自愈、归档的闭环能力。

## 0. 法规索引 (Legal Index)

所有 Agent 必须熟读并背诵以下文件：

1. **工程基本法**：[AGENT_STRICT_BEHAVIOR.md](file:///Users/roy-jd/openclaw/AGENT_STRICT_BEHAVIOR.md) (硬存软链、工具复用)
2. **24小时铁律**：[24h_automated_work_manifesto.md](file:///Users/roy-jd/openclaw/docs/standards/24h_automated_work_manifesto.md) (自愈、反馈、零冗余)
3. **数据管理法**：[data_and_experiment_standard.md](file:///Users/roy-jd/openclaw/docs/standards/data_and_experiment_standard.md) (三层五段、金库制度)
4. **团队协作协议**：[AGENTS.md](file:///Users/roy-jd/openclaw/AGENTS.md) (research-core 工具链调用)

---

## 🏗️ 核心指令 (Core Mandates)

### 1. 物理存储必须“入库”

严禁在系统盘或临时目录进行 GB 级别数据的物理存储。所有计算节点必须将物理数据下沉至 `/jxdxxxx/openclaw_data`。

### 2. 实验过程必须“溯源”

每一个训练任务必须产出 `run_info.yaml`。没有溯源信息的实验结果一律视为垃圾，立即清理。

### 3. 下载速度必须“极致”

禁止单线程 `curl`。必须使用 `aria2c` (16并发) 且配合海外/国内自动链路切换。

### 4. 24小时“自愈”

任务卡死 3 分钟不增长即判定死锁，必须强行自愈。禁止向刘总发送“正在尝试...”之类的空洞汇报，必须直接给数据。

## 🛡️ 执行矩阵

| 场景         | 对应法规     | 强制工具                   |
| :----------- | :----------- | :------------------------- |
| **开工前**   | 工程基本法   | `research-core init`       |
| **下载中**   | 数据管理法   | `aria2c`                   |
| **深夜运行** | 24小时铁律   | `Watchdog` 自愈脚本        |
| **任务结束** | 项目对齐规范 | `research-core vault-sync` |
