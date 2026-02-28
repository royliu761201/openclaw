# GPU Node & TTS Troubleshooting Knowledge Base

This document records the critical system failures, root causes, and solutions discovered during the deployment and validation of `ChatTTS` and `V2V (Meta-Voice)` on the 5-GPU Nvidia L20 server.

## 1. CUDA Driver Kernel Deadlock & Zombie Processes

**Symptoms**:

- `nvidia-smi` shows GPU memory usage (e.g., `480MiB`) but no associated processes are listed.
- Running simple Python scripts with `import torch; torch.cuda.is_available()` hangs indefinitely and silently.
- Force killing FastAPI/Python (`kill -9`) during active inference causes the GPU driver to lock up.

**Root Cause**:
When PyTorch processes are ungracefully murdered via `SIGKILL (-9)` during heavy CUDA driver interactions, the hardware PCI lock is never released back to the Linux kernel, resulting in "Ghost VRAM" leaks and a deadlocked state where no new tensors can allocate.

**Resolution / Workarounds**:

1. Scan for zombie processes holding raw file descriptors rather than relying on `nvidia-smi`:
   ```bash
   for pid in $(ls /proc | grep -E "^[0-9]+$"); do if ls -l /proc/$pid/fd 2>/dev/null | grep -q "/dev/nvidia"; then echo Found Zombie $pid; kill -9 $pid; fi; done
   ```
2. If `nvidia-smi` drops to `0MiB` but PyTorch still deadlocks on `torch.zeros(1).cuda()`, the kernel driver itself must be reset:
   ```bash
   # Try resetting if permissions allow:
   nvidia-smi --gpu-reset -i 0
   ```
3. If inside a Docker container where `rmmod nvidia` and `nvidia-smi -r` are restricted, a **Physical Host Reboot** is the only guaranteed way to flush the hardware state.

## 2. ChatTTS HuggingFace Model Caching Structure Bugs

**Symptoms**:

- `OSError: Error no file named model.safetensors, or pytorch_model.bin, found in directory /asset/gpt`
- The `config.json` refuses to load or throws JSON validation errors.

**Root Cause**:
ChatTTS expects a very strict directory structure inside its `asset/` folder. Downloading the repository blindly or using older model hubs often scatters `gpt/` and `tokenizer/` weights cleanly outside the `asset/` directory.

**Resolution**:
Ensure the multi-gigabyte files are deeply nested inside the `asset/` tree:

```
/models/ChatTTS/
└── asset/
    ├── gpt/
    │   ├── config.json
    │   └── model.safetensors
    └── tokenizer/
        └── tokenizer.pt
```

## 3. Transformers Version Incompatibility (`encode_plus` crashes)

**Symptoms**:

- `AttributeError: BertTokenizer has no attribute encode_plus. Did you mean: '_encode_plus'?` inside `ChatTTS/core.py`.

**Root Cause**:
Recent versions of HuggingFace `transformers` (e.g., `v5.2.0`) completely removed the deprecated `encode_plus` method from `BertTokenizer`.

**Resolution**:
Instead of fighting Conda dependency and proxy-dropout issues during a `pip downgrade transformers==4.41.2`, we monkey-patched the open-source ChatTTS library directly.
Inside `ChatTTS/model/tokenizer.py`:

- Change: `x = self._tokenizer.encode_plus(...)`
- To: `x = self._tokenizer._encode_plus(...)`

## 4. Absolute GPU Isolation & Environment Offline Mode

To run V2V and ChatTTS simultaneously on the same host without OOM (Out Of Memory) collisions, isolation must be applied _before_ loading `torch`.

**Code Snippet**:

```python
import os
import torch

# 1. Enforce strict offline execution (prevents long timeouts if HF proxy dies)
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"

# 2. Hardcode the visible hardware so PyTorch cannot see other GPUs
os.environ["CUDA_VISIBLE_DEVICES"] = "0" # or "1" for V2V

# 3. Inside the script, the visible card is now universally referenced as cuda:0
# Even if physical GPU is index 1, PyTorch maps it to relative index 0.
tensor = torch.randn(1, 16000).to("cuda:0")
```

## 5. SSH Context & Proxy Architecture Deadlocks

### The Hanging Problem

When executing remote tests via arbitrary Python Paramiko scripts, the local machine experienced indefinite, silent timeouts (appearing as server freezes or deadlocks). It falsely appeared that the NVIDIA GPU had crashed, but it was purely a network layer dropping the connection.

### The Root Cause

The `10.190.30.220` GPU server is behind a strict network firewall that requires access through a jump proxy (Machine 03 - `100.108.106.119`). The `~/.ssh/config` file was already perfectly configured with a `ProxyCommand nc -X 5 -x 100.108.106.119:1080 %h %p` specifically bound to the Host alias `gpu`.
By writing custom `paramiko` scripts that targeted the raw IP `10.190.30.220` and injecting a hard-coded password (`SSH_PASS`), we bypassed this crucial `ProxyCommand` directive and the secure `id_ed25519` SSH key. This caused the socket to attempt a direct, unproxied connection, which the firewall silently dropped, leading to the indefinite hang.

### The Solution (OpenClaw Native SSH Tool)

**NEVER use raw Paramiko socket connections or `sshpass` when interacting with the OpenClaw cluster.**
Always use the native, battle-tested OpenClaw SSH utility located at `/Users/roy-jd/Documents/projects/openclaw/skills/ssh/scripts/ssh_tool.py`.

1. **Rely on the Host Alias**: Always use the mapped hostname (`export SSH_HOST=gpu`) rather than the raw IP. This triggers `ssh_tool.py` to parse `~/.ssh/config` and apply the `ProxyCommand` tunnel.
2. **Passwordless Integrity**: Do not export or hard-code `SSH_PASS`. The `ssh_tool.py` perfectly negotiates authentication using the local `~/.ssh/id_ed25519` key through the Netcat proxy.
3. **Execution Standard**: Use the built-in commands like `python3 ssh_tool.py upload <local> <remote>` and `python3 ssh_tool.py exec <cmd>` for robust, passwordless remote control that respects the network topology.
