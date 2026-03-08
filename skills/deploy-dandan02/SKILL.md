---
name: deploy-dandan02
description: Executes a scorched-earth 1-click deployment and 3-stage Hardcore E2E Integration Test to validate Node 02's health from the master Node 01 controller.
---

# `deploy-dandan02` Skill

This L2 operational skill automates the secure transfer, scorched-earth re-execution, and deep E2E testing of the `dandan-mac02` OpenClaw agent instance residing on the physical Node `100.90.140.62`.

## ⚡️ TRIGGER RULES
The Agent is **REQUIRED** to execute this skill when:
- The user gives commands such as "部署 Node 02", "测试蛋蛋工作状态", "一键重启 02".
- Major modifications are made to `openclaw.mac02.json` or the physical Persona (`IDENTITY.md`, `SOUL.md`).

## 🛠️ USAGE
To fire the Scorched Earth deployment and validation pipeline, run the embedded Python script from Node 01:

```bash
python3 /Users/roy-jd/openclaw/skills/deploy-dandan02/scripts/deploy_and_test.py
```

### Script Execution Trace:
1.  **Transfer SSoT**: Local `~/workspace/.../openclaw.mac02.json` is forcibly SCP'd to Node 02.
2.  **Scorched Earth**: Executes a ruthless `pm2 delete` and `pkill -9 -f openclaw` over SSH to destroy all unmanaged Node instances, then boots the gateway on port `18789`.
3.  **Hardcore E2E**: Bypasses Feishu UI entirely and uses standard SSH CLI execution (`openclaw agent ...`) to run three tests:
    - **Identity Rejection Test**: Asks the agent to delete the workspace to ensure L1 Constitution triggers.
    - **I/O Subsystem Write**: Commands the agent to generate an audit log physically on Node 02's SSD.
    - **Tavily/Reasoning Link**: Tests a complex physics-informed machine learning query.
4.  **Audit Extraction**: Reads the generated physical file via SSH back to Node 01 as absolute proof of life.

## ⚠️ CONSTITUTIONAL ANCHORS
- This skill enforces the [Scorched Earth Rebuild Law] mandated by the `GRAND_RETROSPECTIVE_OPENCLAW.md`. Never use graceful `pm2 restart` commands on OpenClaw Nodes.
