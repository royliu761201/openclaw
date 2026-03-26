---
name: workstation-nas-recovery
description: Post-reboot recovery protocol for 90-series GPU workstations. Remounts the NAS, restores CUDA guards, and relaunches interrupted background jobs.
---

# GPU Reboot Recovery Skill 🔄

## When To Use

当 90-1 或 90-2 节点发生以下任何情况时，**必须立即调用本技能**：

- 物理硬重启 (Hard Reboot)
- SSH 因 I/O 洪峰 / OOM / Swap Thrashing 导致的连接超时瘫痪后自行恢复
- `sshfs` 挂载点丢失（表现为 `ls /jhdx0003008` 报 `Transport endpoint is not connected`）
- 任何 `nohup` 后台任务（如数据下载、实验训练）因节点重启而中断

## Recovery Protocol (严格按序执行)

### Step 1: 验证 SSH 连通性

```bash
ssh -o ConnectTimeout=5 90-1 "echo 'SSH OK' && uptime"
```

如果超时，说明节点尚未完成重启，等待后重试。

### Step 2: 重新挂载 NAS (⚠️ 不要用 sudo！)

```bash
ssh 90-1 "sshfs root@10.190.30.220:/jhdx0003008 /jhdx0003008 -p 30305 -o reconnect"
```

> [!CAUTION]
> **绝对禁止使用 `sudo sshfs`！** `sudo` 会动态剥离当前用户的 ED25519 密钥，导致主服务器容器拒绝鉴权（`Permission Denied`）。
> 主服务器端口是 **30305**（不是 22），因为 AI 环境运行在 K8s 容器内。

### Step 3: 验证挂载成功

```bash
ssh 90-1 "ls /jhdx0003008/data && ls /jhdx0003008/envs/workspace && echo 'NAS Mount OK'"
```

### Step 4: 执行 SSoT 恢复脚本

```bash
ssh 90-1 "bash /jhdx0003008/workspace/projects_core/Frenet/baselines/recover_90.sh"
```

该脚本自动完成：

- GPU 连接性验证 (`nvidia-smi`)
- Git safe directory 锁定
- `CUDA_VISIBLE_DEVICES=0` 环境守卫注入

### Step 5: 恢复中断的后台任务

根据 `00_ASSET_DOWNLOAD_BOARD.md` 中标记为 `[Node 90 Fetching...]` 的任务，使用 `nohup` 重新拉起被中断的下载/训练进程。

> [!IMPORTANT]
> **I/O 绞杀禁令 (Law 8)**：重新拉起下载任务时，严禁并发多路百GB级数据流！
> 必须单线程串行执行，保护算力核心的 SSH 心跳畅通。

## Quick Reference (一键复制区)

```bash
# === 90-1 Full Recovery Sequence ===
ssh 90-1 "sshfs root@10.190.30.220:/jhdx0003008 /jhdx0003008 -p 30305 -o reconnect"
ssh 90-1 "ls /jhdx0003008/data && echo 'Mount OK'"
ssh 90-1 "bash /jhdx0003008/workspace/projects_core/Frenet/baselines/recover_90.sh"

# === 90-2 Full Recovery Sequence ===
ssh 90-2 "sshfs root@10.190.30.220:/jhdx0003008 /jhdx0003008 -p 30305 -o reconnect"
ssh 90-2 "ls /jhdx0003008/data && echo 'Mount OK'"
ssh 90-2 "bash /jhdx0003008/workspace/projects_core/Frenet/baselines/recover_90.sh"
```

## Provenance

本技能提炼自 `docs/system_core/07_HARDWARE_NETWORK_LAW.md` Article 7 第 1-4 条。
原始固化日期：2026-03-24 (4090 集群稳定化战役)。
技能独立封装日期：2026-03-26 (I/O 绞杀事件复盘)。
