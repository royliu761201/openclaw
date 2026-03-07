---
description: Standard operating procedures for executing commands on Node 01 (this Mac), covering sudo handling, system file writes, and SSH operations
---

// turbo-all

## ⏱️ 5秒规则（最高优先）

**预计超过5秒的命令，必须后台执行：**
- `WaitMsBeforeAsync=500`（立即转后台）
- 用 `command_status` 轮询结果
- 违反此规则 = 降低老板服务质量，违反宪章

## Node 01 命令执行规范

### sudo 命令（两步法）

**禁止**：`echo password | sudo -S cmd`（无 TTY 会挂死）

**正确步骤**：
1. 运行 sudo 命令，`SafeToAutoRun=false`，`WaitMsBeforeAsync=8000`
2. 等到 `Password:` 出现后，`send_command_input` 发密码：  
   ```
   ~lxh797612011012
   ```
3. `WaitMs=5000` 等结果

---

### 系统路径文件写入（/Library, /etc, /usr/local）

**禁止**：直接用 `write_to_file` 或 `replace_file_content` 写系统路径（权限不足，假成功）

**正确步骤**：
1. 用 `sudo tee` + heredoc 写入，走两步法发密码
2. **必须立即 `cat` 验证**，不验证视为未完成

```bash
sudo tee /Library/LaunchDaemons/xxx.plist << 'EOF'
内容
EOF
cat /Library/LaunchDaemons/xxx.plist   # 验证
```

---

### 网络/SSH 命令

1. 先 ping 确认可达：`ping -c 1 -t 3 <IP>`
2. SSH 始终加 `-o ConnectTimeout=6 -o BatchMode=yes`
3. `WaitMsBeforeAsync` ≥ ConnectTimeout × 1000 + 2000ms

---

### 排查问题顺序

本地 echo → ping → ssh 单跳 → ssh 多跳  
**不可跳层排查**

---

### 老板体验原则

- `SafeToAutoRun=true` 的命令必须直接执行，不等老板
- 结果出来前不打扰老板，出来后给结论不给过程
- 多步任务：先写执行计划审批一次，后续不再打扰
