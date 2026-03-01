# OpenClaw 企业级 5分钟极速部署指南 (Executive Summary)

**目标**：5分钟内不仅拉起核心大模型与搜索网关，更能直连飞书端，并且具备完美的安全隔离与后期无限扩展热拔插能力。

## 一、方案选择与对比

- **【首选推荐】沙盒容器化方案 (Rootless Podman)**：物理隔离，安全防漏洞逃逸，环境变量不污染宿主机，随用随起。（**下文主要以此展开**）
- **【备选替代】物理机直接发版 (Bare-Metal)**：极度轻量，运行 `curl -fsSL https://openclaw.ai/install.sh | bash` 即可一键安装。能在本地开发机快速跑通，但在服务器产线上不推荐，容易引起环境依赖污染。

---

## 二、核心沙盒部署规范 (Podman 方案)

### 1. 声明底层依赖与一键构建镜像 (2分钟)

在服务器源码根目录执行：

```bash
# [按需声明] 将系统级的庞大二进制依赖打入底层（例如如需编译论文，可加上全量 LaTeX）
export OPENCLAW_DOCKER_APT_PACKAGES="texlive-full"

# 一键执行构建，底层由 Podman 进行完全去中心化 (Daemonless) 隔离打包并生成 Linux 守护进程
sudo -E ./setup-podman.sh --quadlet
```

### 2. 灌注全局统一保险箱配置 (1分钟)

该架构下，为了绝对安全，系统所有的敏感配置（API Keys，外部系统 Secrets）**全部必须被封锁且仅被封锁在唯一指定的沙盒配置库中**。

```bash
sudo nano /home/openclaw/.openclaw/.env
```

录入主轴大脑与基础工具的系统级配置：

```bash
OPENAI_API_KEY="sk-xxxx"         # 激活大模型主干思考引擎
TAVILY_API_KEY="tvly-xxxx"       # 激活默认搜索引擎，赋能特工联网
KAGGLE_USERNAME="xxx"            # (可选) 激活官方默认自带的 Kaggle 算法对接组件
KAGGLE_KEY="yyy"
```

### 3. 热加载并对接飞书渠道 (1分钟)

网关通道全部为“热插拔”。安装飞书不需要重启或修改核心镜像：

```bash
# 动态安装官方飞书桥接通道
sudo -u openclaw /home/openclaw/run-openclaw-podman.sh cli plugins install @openclaw/feishu

# 启动交付向导，UI终端会提示您录入飞书后台对应申请的 App ID 和 Secret
sudo -u openclaw /home/openclaw/run-openclaw-podman.sh launch setup
```

### 4. 交付自动化守护进程 (1分钟)

全盘托付给 Linux 内核底层的 Systemd 系统，实现宕机、断网、断电情况下的无限满血自动拉活。

```bash
# 以后台常驻服务方式启动，真正的 24 小时待命！
sudo systemctl --machine openclaw@ --user start openclaw.service
```

---

## 三、Day-2 长效运维 (技能/插件的热拔插与独立配置)

部署一旦成型，它的延展性将超越传统服务架构：

1. **加装新的自定义私有技能去哪装？**
   无论是官方发布的外部技能还是你的团队手写的 Python/Node.js 插件，只需将它们放在工程映射的 `extensions/` 目录下，接着敲：
   ```bash
   sudo -u openclaw /home/openclaw/run-openclaw-podman.sh cli plugins install ./extensions/my-custom-skill
   ```
2. **自定义的小技能，如果它自己也需要访问外网密码或配置，怎么办？**
   **不管你挂了多少个不同的工具，配置严禁分散！** 依然一针见血回到 `/home/openclaw/.openclaw/.env` 这个统一防空洞。直接另起一行增加你自定义组件所需的环境变量：
   ```bash
   MY_CUSTOM_DB_PASS="123456"
   ```
   重启服务后 (`sudo systemctl --user restart openclaw`)，主容器会自动将它们作为环境变量像血液一样“动态泵入”给你的 `my-custom-skill` 内部使用。
3. **遇到需要 `gog` 客户端这种没法编译的 “单体应用包” 怎么接？**
   暴力且优雅的方法：直接将其拖入服务器专为您开辟的 **内部通道文件夹** `/home/openclaw/.openclaw/workspace/` 并赋予权限 (`chmod +x`)。由于这是特供的系统内部挂载区（且默认处在容器 Agent 视角的 `$PATH` 中），Agent 能够把它像原生系统命令一样当场调用。

> **总结**：这种基于 Rootless Podman 的架构既保证了业务核心的高度纯净与去中心化安全，又用一条主线（`.env`）统死了所有的配置入口。这是老板查收与系统长期迭代最规范的版本。
