# GPU 访问链路深度复盘报告 (2026-03-03)

## 🚨 1. 故障回放 (Incident Timeline)

- **现象**：老板发现 `ssh gpu` 报错 `Permission denied`，01 延迟飙升至 800ms+。
- **初诊**：06 跳板网络通畅，但其内存中的 `ssh-agent` 身份丢失；Tailscale 走 HKG 中转导致握手超时。

## 🔍 2. 根因分析 (Root Cause Analysis)

1. **身份脆弱性 (Identity Fragility)**:
   - 依赖 `ProxyJump` 时的 `ssh-agent` 转发。
   - 06 (Windows) 的 Session 一旦断开或系统自动重启，身份信息即刻归零。
2. **链路不稳定 (Path Instability)**:
   - 01 -> 06 的校园网 P2P 握手失败，Tailscale 回滚至 DERP (hkg)。
   - 在高延迟下，SSH 握手的时序要求极高，极易触发权限失败假象。
3. **配置断层 (Config Gap)**:
   - 迁移至 06 跳板后，02/03/05 节点的 `~/.ssh/config` 未同步更新，仍试图走旧路径。

## 🛠️ 3. 解决方案与核心动作 (Resolution)

1. **身份硬化 (Identity Hardening)**:
   - 彻底废除“临时通行证”方案。
   - **动作**：将 01, 02, 03, 05 的公钥物理写入 GPU 的 `authorized_keys`。
2. **配置标准化 (Config Standardization)**:
   - 统一使用 `100.96.76.125` (06 IP) 作为 ProxyJump 目标，解决别名解析问题。
3. **P2P 强力纠偏**:
   - 确认校园网环境下，通过 `tailscale ping` 压测 P2P 握手。

## 📊 4. 体检结果 (Current Health)

| 节点          | 物理状态   | 网络路径  | Latency   | 结论    |
| :------------ | :--------- | :-------- | :-------- | :------ |
| **01 (本机)** | 校园网 P2P | 直连 06   | **27ms**  | ✅ 极速 |
| **02 (家)**   | 宽带 P2P   | 直连 06   | **10ms**  | ✅ 极速 |
| **03 (MBA)**  | MBA 联网   | HKG Relay | ~280ms    | ✅ 稳定 |
| **05 (Air)**  | 校园网 P2P | 直连 06   | **< 1ms** | ✅ 极速 |

---

## 💡 5. 经验教训 (Lessons Learned)

- **准则一**：任何涉及 24/7 业务的授权，必须全量采用**物理写入**，严禁使用“内存代理”。
- **准则二**：汇报时必须区分“逻辑路径”与“物理设备”。03 是 MBA，不是香港中转机。

**执行人：蛋蛋 (Dandan)**
**验收日期：2026-03-03**
