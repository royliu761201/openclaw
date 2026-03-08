---
name: node-manager
description: A universal, parameterized operational skill that performs Scorched-Earth Deployment, System Recovery, and Hardcore E2E Integration Testing on any OpenClaw compute node (e.g., Node 02, Node 03).
---

# `node-manager` Skill

This L2 operational skill is the ultimate administrative weapon for managing the OpenClaw grid. It transcends simple deployment by automating the secure transfer of configurations, executing absolute process recovery (Scorched Earth rebuild), and conducting rigorous End-to-End (E2E) testing on any designated physical Node (e.g., `100.90.140.62` for Node 02).

## ⚡️ TRIGGER RULES
The Agent is **REQUIRED** to execute this skill when:
- The user gives commands such as "部署 Node 02", "测试蛋蛋工作状态", "恢复 03 系统", "一键重启节点".
- Major modifications are made to any node's JSON gateway configuration or its physical Persona (`IDENTITY.md`, `SOUL.md`).
- A node exhibits "zombie" symptoms, PM2 log silence, or WebSocket disconnections requiring absolute healing.

## 🛠️ USAGE
To fire the Scorched Earth Recovery and Verification pipeline, run the embedded Python script from Node 01, passing the necessary target parameters:

```bash
python3 /Users/roy-jd/openclaw/skills/node-manager/scripts/manage_node.py --node 02 --user roy-002 --ip 100.90.140.62 --workspace dandan02 --pm2_name dandan-mac02 --config openclaw.mac02.json
```

**Parameters Explained:**
- `--node`: The physical target identifier (e.g., `02` or `03`). Used by `ssh_tool`.
- `--user`: The remote SSH username (e.g., `roy-002`).
- `--ip`: The remote IP address (e.g., `100.90.140.62`).
- `--workspace`: The target agent workspace folder name (e.g., `dandan02`).
- `--pm2_name`: The name of the PM2 daemon to kill and spin up (e.g., `dandan-mac02`).
- `--config`: The local file name of the gateway JSON payload to push (e.g., `openclaw.mac02.json`).

### The 3-Step Execution Trace:
1.  **Deploy (SSoT Sync)**: The local configuration source of truth is forcibly SCP'd to the target node.
2.  **Recover (Scorched Earth)**: Executes a ruthless `pm2 delete` and `pkill -9 -f openclaw` over SSH to destroy all corrupted/zombie Node instances and free up deadlocked ports, then cold-boots the gateway.
3.  **Test (Hardcore E2E)**: Bypasses UI clients entirely and uses standard SSH CLI execution (`openclaw agent ...`) to run three systemic tests:
    - **Identity Rejection Test**: Verifies L1 Constitution adherence (sandbox laws).
    - **I/O Subsystem Write**: Commands the agent to generate an audit log physically on the target's SSD.
    - **Tavily/Reasoning Link**: Tests a complex physics-informed machine learning query.
4.  **Audit Extraction**: Reads the generated physical `deployment_audit.txt` file via SSH back to Node 01 as absolute proof of recovery.

## ⚠️ CONSTITUTIONAL ANCHORS
- This skill enforces the [Scorched Earth Rebuild Law] mandated by the `GRAND_RETROSPECTIVE_OPENCLAW.md`. Never use graceful `pm2 restart` commands on OpenClaw Nodes. Only perform absolute deletion and cold restarts.
