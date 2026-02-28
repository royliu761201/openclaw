# OpenClaw Installation & Deployment Specification

**Objective:** To establish an absolutely robust sequence for OpenClaw provisioning that prevents AI gateway crashes, unhandled skill dependencies, and "brain downtime."

## The Core Problem

Historically, starting the OpenClaw daemon (`run-node.mjs`) would fail silently or crash entirely if core `.env` tokens (like `GEMINI_API_KEY`) were missing, or if downstream skills (like `wandb` or `kaggle`) lacked their CLI dependencies. This resulted in the "brain" refusing to operate, which is unacceptable for a production-grade AI infrastructure.

## 1. The Pre-Flight Daemon Checklist (Zero-Downtime Rule)

Before the `openclaw` PM2 daemon is ever allowed to start, the deployment sequence MUST complete these checks:

### 1.1 Credential Injection Phase

- The daemon must **never** be started without a verified `.env` file present in the assigned `OPENCLAW_CONFIG_PATH` directory.
- The following absolute minimum variables MUST be validated:
  - `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) - _Without this, the brain cannot boot._

### 1.2 The "Skill-Sync" Phase

Dependencies for skills MUST be satisfied globally prior to runtime. Skill execution should never crash due to a missing Python or Node package.

- **Rule**: Every time a new node is spun up, or the `skills/` directory is updated via Git, the `scripts/bootstrap-skills.sh` script MUST be executed.
- This script automatically traverses every module in `skills/` and executes `pip install` (via domestic mirrors) and `npm install` respectively.

## 2. Hardened Environment Paths (`PATH` Robustness)

Skills like `wandb` (Weights & Biases) and `latex` execute shell commands natively in the background. If the daemon environment doesn't know where these binaries are, the skill crashes.

- **Node Initialization Requirement**: The Node.js PM2 process MUST be started with an extended `$PATH` environment variable that includes:
  - `~/.local/bin` (Linux/Mac User Space Python Bins)
  - `~/Library/Python/3.9/bin` (macOS User Space Python Bins, specifically for `wandb` and `kaggle`)
  - `/opt/homebrew/bin` (Homebrew CLI binaries like `pdflatex`)
  - `~/.nvm/versions/node/*/bin` (NPM binaries)

## 3. Graceful Skill Degradation (Architecture Paradigm)

If a skill dependency (like `wandb`) is missing or fails to authenticate:

1. The skill itself should log an error to `os.stderr` or return a structured JSON error flag.
2. The core OpenClaw "brain" (the Gemini router) MUST NOT crash. It must elegantly process the skill failure, inform the user "W&B CLI is not installed", and continue functioning.

## 4. The Standardized Node Boot Sequence

From zero to production, a new OpenClaw node must follow exactly this flow:

1. **Network**: Join Tailscale (`tailscale up --ssh`).
2. **Keyring**: Generate `id_ed25519` and share pubkey with GPU array.
3. **Mirrors**: Write `pypi.tuna.tsinghua.edu.cn` to config.
4. **Git Sync**: Clone `research-archive` code base.
5. **Cold Secrets**: Securely `scp` the `.env` and `secrets.json` from the master node.
6. **Bootstrap**: Run `./scripts/bootstrap-skills.sh` to pre-install `wandb`, `kaggle`, etc.
7. **PM2 Ignite**: Start the gateway via PM2, explicitly injecting the master `$PATH` string.
