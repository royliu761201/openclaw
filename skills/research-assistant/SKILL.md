---
name: research-assistant
emoji: 👩‍🔬
description: Expert Research Agent for NSFC Grants, Patents, and Academic Papers. Operates by orchestrating `gemini`, `latex`, and `github` skills according to strict scientific standards.
metadata:
  openclaw:
    requires:
      skills: ["gemini", "latex", "github", "tavily-search"]
---

# Research Assistant

This skill defines the **Standard Operating Procedures (SOPs)** for high-level scientific research tasks. It defines specialized modes/tools to enforce venue-specific standards (NeurIPS, ACL, NSFC, Patent) without code duplication.

## 1. Paper Drafting Tools

### `draft_paper_neurips`
**Goal**: Draft a NeurIPS (Neural Information Processing Systems) paper.
-   **Style**: Strict 9-page limit (excluding refs).
-   **Focus**: Algorithms, Theory, Generative Models, Deep Learning.
-   **Citation Style**: Numbered `[1]`.
-   **Prompt**: "Draft a NeurIPS paper. Focus on theoretical novelty and algorithmic rigor. Use `neurips_20xx.sty` format. Ensure 'Broader Impact' section is included."

### `draft_paper_acl`
**Goal**: Draft an ACL (Association for Computational Linguistics) paper.
-   **Style**: 8-page long paper / 4-page short paper.
-   **Focus**: NLP, Linguistics, Language Models.
-   **Citation Style**: `(Author, Year)` / `\citet`, `\citep`.
-   **Prompt**: "Draft an ACL paper. Focus on linguistic methodology and empirical evaluation. Use `acl.sty`. Emphasize error analysis and linguistic insights."

### `draft_paper_general`
**Goal**: Generic high-impact academic paper (Nature/Science style).
-   **Style**: "Best Oral" Narrative Arc.
-   **Focus**: Cross-disciplinary impact.
-   **Prompt**: "Draft a high-impact paper. Follow the 'Universal Scientific Writing Standards'. Figure 1 must summarize the entire contribution."

## 2. NSFC Grant Drafting (`draft_grant_nsfc`)

**Goal**: Draft an NSFC proposal that meets the "Strategic Manifesto" standard.
-   **Strategic Alignment**: Must align with "Guide Direction" (e.g., AI4S).
-   **Structure**: Need (Tier 1-3) -> Innovation (Paradigm Shift) -> Feasibility.
-   **Formatting**: Use bold/italics (`\textbf{\textit{...}}`) for emphasis.

## 3. Patent Drafting (`draft_patent_cnipa`)

**Goal**: Produce a valid CNIPA patent disclosure.
-   **Workflow**: Claims First (1 Indep, 5 Dep) -> Description -> Summary.
-   **Tone**: Legal-Technical ("said", "comprising").
-   **Adversarial Check**: Simulate examiner critique.


## 4. Remote Infrastructure Standards (Context)
**CRITICAL**: All experimental code MUST be designed to run on the **Remote Server** (`L20 Cluster`).
-   **Root Workspace**: `/root/research_bot`
-   **Data Storage**: `/root/research_bot/data`
-   **Results Output**: `/root/research_bot/results/[project_name]`
-   **Model Weights**: `/root/research_bot/models` (or project-specific `data` folders)
-   **Network Mirrors** (Pre-Configured):
    -   **Pip**: `https://pypi.tuna.tsinghua.edu.cn/simple`
    -   **HuggingFace**: `HF_ENDPOINT=https://hf-mirror.com` (Models download here automatically)

### Active Conda Environments
Select the correct environment for the task:
| Environment | Domain | Key Packages |
| :--- | :--- | :--- |
| **`pesso`** | Physics/CFD | `numpy`, `scipy`, `matplotlib` |
| **`calam`** | LLM/NLP | `vllm`, `transformers`, `torch` |
| **`frenet`** | MedSAM/Seg | `monai`, `sam2`, `torch` |
| **`medtime`** | Time Series | `lightning`, `pandas` |
| **`cogd`** | Geometric | `torch-geometric`, `diffusion` |

### Code Generation Rules
1.  **Paths**: Always use absolute paths starting with `/root/research_bot`.
2.  **No GUI**: Use `matplotlib.use('Agg')` for plotting; save `.png` to `results/`.
3.  **Logging**: Write logs to local files or stdout (captured by runner); do not use interactive progress bars (`tqdm` ok but monitor overhead).

### W&B Environment Standard (Explicit Isolation)
To prevent network conflicts and global state (`~/.netrc`) pollution, ALL projects running on the remote cluster MUST embed the following explicit isolation block in their `run_exp.sh` before `conda run`:

```bash
# W&B Isolation Settings (Explicit Scope)
if [ -f "$(pwd)/.env" ]; then
    export $(grep -v '^#' "$(pwd)/.env" | xargs)
    echo "🔑 Loaded local .env variables"
fi
export WANDB_DIR="$(pwd)/outputs/wandb_logs"
export WANDB_CONFIG_DIR="$(pwd)/outputs/wandb_config"
export WANDB_CACHE_DIR="$(pwd)/outputs/wandb_cache"
mkdir -p "$WANDB_DIR" "$WANDB_CONFIG_DIR" "$WANDB_CACHE_DIR"

# Connect W&B directly by ignoring bashrc proxies
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
```
Never use `export WANDB_MODE=offline` as the default anymore; explicit credentials via `.env` are the standard.

### Project Structure Standard (Layout)
All projects MUST follow this directory structure:
```text
/root/research_bot/projects/[project_name]/
├── code/               # Python Source Code
│   ├── src/            # Reusable Modules
│   ├── main.py         # Entry Point
│   └── config.yaml     # Hyperparameters
├── paper/              # LaTeX Source
│   ├── main.tex
│   └── figures/
├── scripts/            # Shell Runners
│   └── run_exp.sh
└── results/            # Output (Synced Down)
    └── [exp_id]/
```



### Remote Data & Model Standard (Shared Resources)
To prevent disk bloat and ensure reuse, strictly adhere to this shared layout:

1.  **Model Zoo** (`/root/research_bot/models/`):
    -   **Purpose**: Shared pre-trained weights (HuggingFace, ResNet, etc.).
    -   **Usage**: ALL projects must symlink here. Do NOT download weights to project folders.
    -   **Structure**:
        ```text
        /root/research_bot/models/
        ├── bert-base-uncased/
        ├── resnet50.pth
        └── sam2_hiera_large.pt
        ```

2.  **Data Lake** (`/root/research_bot/data/`):
    -   **Purpose**: Heavy datasets (ImageNet, TubeTK, MIMIC-IV).
    -   **Usage**: Store actual data here; projects link to it via `ln -s`.
    -   **Structure**:
        ```text
        /root/research_bot/data/
        ├── [project_name]/    # Dedicated folder per project
        └── shared/            # Common datasets (e.g., ImageNet)
        ```

### Track 1: Virtual Cell (Nobel Track)

**Goal**: Move from "Static Structure" to "Dynamic Life" (Digital Twin).
-   **Grand Challenge**: Predicting systemic emergent behavior from molecular perturbations.
-   **Architecture**:
    1.  **Molecular Dynamics**: Coarse-Grained Neural Potentials / Diffusion.
    2.  **Gene Regulatory Networks**: Causal Discovery (GFlowNets).
    3.  **Whole-Cell Sim**: Physics-Informed Neural Operators (PINO).

### Project: CellFlow (V1 & V2)
**Title**: "Differentiable Causal Discovery of the MAPK Pathway via Physics-Guarded Generative Flow"
-   **Concept**: Reconstruct regulatory networks using *Actionable Causality* not just correlation.
-   **Method V1**: **Physics-Guarded GFlowNet**. Constrain causal graphs using AlphaFold-Multimer docking scores (pruning 99% of search space).
-   **Method V2** (Active Geometric):
    -   **Bio-Encoder**: SE(3)-Equivariant GNN (EGNN) on Point Clouds.
    -   **Active Learning**: Bayesian Information Gain to select the "Next Best Experiment".
    -   **Target**: "The 10% Data Challenge" (Reconstruct MAPK with 10% of Perturb-seq data).

## 6. Execution Protocol

To perform these tasks, the agent should:
1.  **Create Workspace**: `mkdir -p workspace/[project_name]`
2.  **Generate Content**: Use `gemini` with the specific venue prompt.
3.  **Compile**: Use `latex compile workspace/[project_name]/main.tex`.
4.  **Verify**: If compile fails, use `gemini` to fix the LaTeX error log.
5.  **Commit**: Use `github` or `git` to save progress.

## 7. Knowledge Bank & Templates

### A. Venue Standards (Reference)
| Venue | Tier | Deadline | Page Limit | Anonymity |
| :--- | :--- | :--- | :--- | :--- |
| **NeurIPS** | CCF-A | May 21 | 9 Pages | Double Blind |
| **ICML** | CCF-A | Jan 30 | 8 Pages | Double Blind |
| **ICLR** | Top | Oct 01 | 9 Pages | Double Blind |
| **CVPR** | CCF-A | Nov 14 | 8 Pages | Double Blind |
| **ACL** | CCF-A | Jan 15 | 8 Pages | Double Blind |
| **Nature** | SCI-Q1 | Rolling | ~3000 Words | Single Blind |

### B. Local Templates
-   **NeurIPS**: `skills/research-assistant/templates/neurips_2026.tex`
-   **ICML**: `skills/research-assistant/templates/icml_2026.tex`
-   **Grant Profile**: `skills/research-assistant/knowledge/profiles/pi_profile_xiaohua_liu.md`

## 8. Legacy Removal Note

*This skill replaces the legacy `ResearchBot` Python scripts (`patent_writer.py`, `grant_writer.py`, etc.). All logic is now driven by LLM reasoning using these standards.*
