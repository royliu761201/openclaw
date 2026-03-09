---
description: Enforces node-level hardware verification and topology probing to prevent physical hallucination and payload mismatch.
name: ontology
---

# Ontology (System Holographic Topology Probe)

This core skill exists to permanently eradicate **Physical Topology Hallucination** during cross-node operations.
In the past, Agents blindly assumed `Node 02` or `remote` could handle heavy deep learning or massive dataset downloads, immediately crashing edge gateways.

To defend the OpenClaw Grid, **ANY Agent attempting cross-node communication, bandwidth transfer, model probing, or compute dispatch MUST invoke this skill first!**

## 🚨 Top-Level Topology Defense

You MUST treat the Ontology as your "Physical Reconnaissance Probe".

1. **Probe First, Dispatch Later**: Before sending any payload or command (even a simple `wget`) to a remote node, you **MUST** execute `ontology.py query --type Node` to acquire its true, physical parameters and role.
2. **No Assumption Policy**:
   - NEVER assume the word `Node` implies compute capacity.
   - NEVER assume the word `Server` implies high bandwidth.
3. **The Absolute Truth (Physical Mapping)**:
   This graph is the objective physical law. Any violation is considered fatal topology hallucination:
   - **`Node 01`**: Master Control (The local commander brain).
   - **`Node 02`**: Edge Gateway (**Zero-Weight policy strictly enforced. ABSOLUTELY NO heavy compute or large file storage**).
   - **`Node 03`**: Data Vault (Cold storage vault, pure CPU, no CUDA).
   - **`Node 05`**: Exit Node (Unrestricted outbound proxy fetcher).
   - **`Node 06`**: Jump Host (Network penetration bridge only).
   - **`GPU Server (10.190.*)`**: Air-Gapped Tensor Forge (The **ONLY** authorized zone for heavy AI experiments and dataset persistence at `/jhdx0003008/`).

## Usage

The Ontology SSoT database is a pure JSONL (`graph.jsonl`) located under `workspace/docs/system_core/memory_core/ontology/`.

### Probe All Nodes

```bash
python3 ~/openclaw/skills/ontology/scripts/ontology.py list --type Node
```

_If the target's Role is NOT Tensor Forge, DO NOT dispatch heavy ML workloads!_

### Lookup Policies

```bash
python3 ~/openclaw/skills/ontology/scripts/ontology.py query --type Policy --where '{"scope":"workspace"}'
```

Remember: **Ontology is the ONLY Source of Truth for the OpenClaw physical realm. Blind dispatch without querying this graph is an absolute violation.**
