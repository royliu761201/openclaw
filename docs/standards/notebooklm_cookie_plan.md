# OpenClaw 跨域科研大脑 (NotebookLM API) 部署计划书

## 1. 目标与背景
基于老板的指示，在当前 24 小时满功率突击（第一矩阵）的体系之外，为本控制台增加一个**不需要官方内测 Key、通过 Cookie 驱动**的“次级大脑”工具 —— NotebookLM。以提升 Agent 自身的智能厚度和处理超大 pdf 文献集的能力。

## 2. 工具选型
经过全网调研，我们锁定全球 Star 最高、最前沿的逆向工程实现库：
**Github Repository:** `adithya-s-k/NotebookLM-API`
**驱动原理:** 底层使用 Selenium 抓取或者注入用户的 Google 环境 Cookie (如 `__Secure-1PSID`)，模拟网页行为，从而完全免费地调用 NotebookLM 所有服务能力。

## 3. 部署动作 (分两步)

### A. 准备与拉取 (Agent 动作)
- 克隆 `adithya-s-k/NotebookLM-API` 仓库到本项目目录。
- 构建 Python 虚拟环境，并安装其前置依赖 (如 `Selenium`, `requests` 等)。
- 将核心包封装成我们统一使用的入口脚本 `scripts/agents/notebooklm.py`。

### B. 鉴权与注入 (需要老板动作)
由于这不是官方 API，它的运转 100% 依赖于主人的“认证身份”。
- 我们会在 `~/.gemini/notebooklm_cookies.txt` 创建授权文件。
- 需要老板在自己的某一个登录了 Google 的主浏览器（Chrome/Edge）中，通过开发者工具 (F12) 查找到并复制诸如 `__Secure-1PSID`, `__Secure-1PSIDTS` 的 Cookie 值，填入该文件。

## 4. 风险控制与规范复盘 (合规性)
- **风控提示**: 使用抓包/Cookie机制属于“非官方”途径，虽然完全免费，但偶尔可能因 Google 封号或前端升级导致工具暂时失效。这不影响我们已固化的底层科学矩阵进程。
- **独立环境**: 所有的 NotebookLM 相关脚本只会放在 `scripts/agents/` 供前端指挥部使用，绝不会渗透或污染我们的 GPU 数据金库和 4x4 生产矩阵。

---

> [!IMPORTANT]
> **评审意见收集**
> 如果老板批准此方向，我将开始安全规范的 Clone 和依赖安装，并指导老板如何填入需要的 Cookie。请总裁批示：“Go” 或“取消”。
