# OpenClaw Engineering & Infrastructure Standards

This document serves as the absolute source of truth for deploying, managing, and securing OpenClaw nodes (e.g., Mac 01, 02, 03) and connecting them to GPU clusters. All future modifications and node additions MUST adhere to these four pillars.

## Pillar 1: Zero-Trust Authentication (`Auth-Zero`)

- **No Hardcoded Passwords**: The `.env` and `secrets.json` files MUST NEVER contain `SSH_PASS` or raw system credentials for inter-node communication.
- **Ed25519 Obligation**: Every new compute node must generate an `ed25519` SSH keypair upon initialization.
- **Key-Based GPU Access**: The public keys of all OpenClaw daemons must be explicitly injected into the GPU root `~/.ssh/authorized_keys`.
- **Skill Resilience**: Python/Node automation scripts (e.g., `ssh_tool.py`) MUST implement native fallback to `~/.ssh/id_ed25519` and dynamically regenerate proxy sockets to prevent 'Broken Pipe' teardowns.

## Pillar 2: Mesh Topology & Routing (`Mesh-Route`)

- **Fixed-IP Mandate**: Intra-node communication MUST exclusively use Tailscale `100.x.x.x` addresses. Local DHCP IPs (`192.168.x.x`) are banned for daemon inter-connectivity due to roaming volatility.
- **Transparent Proxying**: Applications must NOT manage their own jump-server routing. All multi-hop GPU connections MUST be defined at the OS level in `~/.ssh/config` using `ProxyCommand`.
- **Split Tunneling Ecosystem**:
  - Overseas API traffic (Google/OpenAI) routes through a designated Tailscale Exit Node.
  - Domestic APIs (Feishu) and Package Mirrors bypass the Exit Node via explicit local routing tables.

## Pillar 3: Lean Deployment & Acceleration (`Lean-Node`)

- **Headless Optimization**: Server nodes (Mac 02/03) MUST NOT install GUI-heavy distributions. (e.g., Use the 116MB `basictex` instead of the 5GB `mactex`).
- **Domestic Mirror Injection**: To prevent pipeline timeouts, all nodes MUST be bootstrapped with domestic mirrors:
  - `Homebrew`: Tsinghua/SUSTech
  - `Pip`: PyPI Tsinghua (`pypi.tuna.tsinghua.edu.cn`)
  - `Conda`: Aliyun / BFSU
- **Unified Daemon Management**: Long-running background services (SOCKS5, VPN Watchdogs, OpenClaw Gateway) MUST be managed by PM2 (`pm2 start ...`) to guarantee auto-restart on system crash or reboot.

## Pillar 4: Hybrid Synchronization & Disaster Recovery (`Hybrid-Sync`)

- **Git Single Source of Truth (SSoT)**: All workspace source code, LaTeX papers, and configuration schemas MUST be committed to the private GitHub `research-archive` repository. Local peer-to-peer `rsync` scripts are deprecated to avoid merge conflicts.
- **Asynchronous Cold Storage (Rclone)**: Massive binary datasets, experimental results, and highly sensitive keys (`secrets.json`, `.env`) MUST be excluded via `.gitignore` and instead mirrored unidirectionally to Google Drive via scheduled `rclone` tasks.
