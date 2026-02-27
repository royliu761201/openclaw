---
name: research-standards
description: AI4S Scientific Engineering Protocols. Defines the standard lifecycle for idea scouting, project initialization, execution, and manuscript production.
---

# Research Standards (AI4S Protocol)

This skill defines the **Standard Operating Procedures (SOPs)** for conducting high-quality research. It is organized by the **Research Lifecycle**.

## Phase 00: Academic Integrity (The First Principle)

**Strict Rule**: No Fabrication, Plagiarism, or Hallucination.

- **Data**: Never modify raw data to fit a hypothesis.
- **Results**: Report all runs, not just the best seed (unless explicitly stated).
- **Citations**: Never cite a paper you haven't read.
- **Honesty**: If an experiment fails, report the failure. Negative results are valuable.

## Summary Checklist (The "Golden Ticket")

- [ ] **INTEGRITY**: No Fabrication, No Cherry-picking, No Hallucinated Citations.
- [ ] **Idea**: Novel (>30%), Feasible, Valued.
- [ ] **Data**: Broad Search -> Academic Check -> Repository.
- [ ] **Exp**: Main (L20) + Baselines (P100) + Ablations.
- [ ] **Run**: Smoke Test (Batch=2) -> Detached Exec -> Checkpoint (Best/Last).
- [ ] **Write**: Zero Warning LaTeX + ZeroGPT (No "Delve") + Figure 1 Masterpiece.
- [ ] **Elite**: Theoretical Proof + OOD Generalization.

## Phase 0: Idea Scout (The Scout Protocol)

Before ANY code is written, an idea must pass the **Scout Protocol**.

### Core Criteria

1.  **Novelty**: >30% different from SOTA. No "incremental +1%" papers.
2.  **Feasibility**: Fits resource budget (No "Google-scale" ideas).
3.  **Value**: Solves a *real* problem, not a strawman.

### The "IdeaDebate" Check

- **One-Liner**: Summary in one sentence.
- **Secret Sauce**: Technical novelty.
- **Why Now?**: Why hasn't this been done?
- **Strongman Baseline**: Compare against the best, not the weak.

## Phase 1: Initialization (Project & Venue)

### 1. Identify Venue (Target: S-Tier)

**Goal**: Aim for the top. Do not compromise.

- **AI/ML**: ICLR, ICML, NeurIPS (NIPS).
- **Vision/NLP**: CVPR, ICCV, ECCV, ACL, EMNLP.
- **General**: AAAI, IJCAI.
- **Science**: Nature/Science (and sub-journals), Cell, PNAS.
- **Criteria**: CCF-A or CAS Q1 (中科院一区).

### 2. Template First Rule

- ask: **"Which journal/conference?"**
- action: **Download Official Template** (never guess).

### 2. Project Structure (Research Vault)

Initialize the project with this layout:

```text
research_vault/<track>/<project>/
├── 01_input/          # Literature, Data
├── 02_method/         # Code, Experiments
├── 03_output/         # Logs, Figures
├── 04_manuscript/     # LaTeX Source
└── 50_archive/        # Frozen Assets
```

- Create `README.md` using the *Idea-to-Paper* template.

### 3. Dataset Acquisition (The Funnel)

**Rule**: Do not just use the first dataset you find. Follow the "Dataset Funnel":

1.  **Broad Search (Web/Exa/Tavily)**:
    - Identify candidates: "What datasets exist for X?"
    - Check licenses (Commercial/Research).
    - Use `tavily-search` or `exa-search` skills.
2.  **Academic Grounding (Papers With Code)**:
    - Verify standard benchmarks: "What do SOTA papers use?"
    - Use `academic-search` (ArXiv) to find the *official* split.
3.  **Repository Acquisition (Kaggle/HF)**:
    - **Source**: Use `kaggle kernels_list` or `dataset_push`.
    - **Download**: Store raw data in `01_input/` (e.g., `kaggle kernels_output`).
    - **Preprocess**: Version control your dataset changes using Kaggle Datasets.

## Phase 2: Execution (Experiments)

### 1. Experimental Design (The Trinity)

Every project **MUST** execute three types of experiments:

1.  **Main Method (L20)**: Your proposed solution.
2.  **Baselines (P100)**: Reproduce SOTA (Strongman).
    - Do not copy numbers from papers. Rerun them.
3.  **Ablations (L20)**: "Turn it off" tests.
    - Prove causality: "If I remove X, performance drops by Y%".
    - Ablate *every* new component.

### 2. Compute Strategy (Resource Isolation)

**Strict Rule**: One card per experiment. No sharing.

- **L20 (SSH Clusters)**: Reserved for **Main Experiments**.
  - High VRAM, fast interconnect.
  - Use for: Final training, large ablations.
- **P100 (Kaggle Kernels)**: Reserved for **Baselines & Data**.
  - Free, lower throughput.
  - Use for: Data preprocessing, small baseline replication, unit tests.

### 3. Optimization Protocols (Fail Fast)

- **Smoke Test (Sanity Check)**: Before ANY full training:
  - **Data**: Use 1% data or a synthetic batch.
  - **Params**:
    - `batch_size=2`: Catch OOMs early.
    - `lr=1e-3`: Verify loss decreases rapidly (overfit a single batch).
  - **Goal**: Run 1 epoch, ensure no crash, check `wandb` logging.
- **Code Acceleration**:
  - Use `torch.compile` (PyTorch 2.0+).
  - Use `mixed_precision` (AMP/BF16) to maximize L20 throughput.
- **Isolation**:
  - Always set `CUDA_VISIBLE_DEVICES=X`.
  - Example: `CUDA_VISIBLE_DEVICES=0 python train.py ...`

### 4. Checkpoint Strategy (Resilience)

- **Mandatory Files**:
  - `last.pt`: Saved every epoch. Used for **Resume**.
  - `best.pt`: Saved when validation metric improves. Used for **Inference**.
- **Modes**:
  - **Resume**: `train.py` MUST check for `last.pt` on startup.
    - If found: Load state_dict, optimizer, scheduler, and epoch.
  - **Inference Only**:
    - Support `--eval` or `--inference` flag.
    - Load `best.pt` automatically.
    - Disable gradients (`torch.no_grad()`).

### 5. Environment Prep (SSH)

- **Remote Setup**: Use `ssh conda create` to ensure clean environments on clusters.
- **Sync**: Use `ssh upload` to push code from `02_method/` to the remote workspace.

### 6. Dataset Transfer (Robustness)

- **Direct Download**: Try `wget` or `kaggle` CLI on the remote server first.
- **Local Fallback**: If remote access is blocked:
  1.  Download to local `01_input/`.
  2.  Use `ssh upload --resume` to transfer large files (supports breakpoint resumption).

### 7. Remote Execution (Detached)

- **Long Running Jobs**: **NEVER** run training in the foreground.
  - Use `ssh exec --detach` (or `nohup`/`tmux`).
  - Example: `skills/ssh/scripts/ssh_tool.py exec "python train.py" --detach`
- **Logging**: All scripts **MUST** use `wandb` for logging (no stdout reliance).

### 8. Artifact Sync

- **Retrieval**: Use `ssh download` or `kaggle kernels_output` to pull logs/models to `03_output/`.

## Phase 3: Manuscript (Drafting)

### Modular LaTeX Structure

```text
04_manuscript/
├── main.tex           # Inputs only (no content)
├── refs.bib           # Single source of truth
├── sections/          # Content chapters
│   ├── 00_abstract.tex
│   ├── 01_intro.tex
│   ├── 02_related.tex (Method-based categorization)
│   ├── 03_method.tex
│   └── 04_experiments.tex
└── figures/           # All images
```

### Standard Flow (Generic Template)

1.  **Abstract**: 4-sentence structure (Context, Gap, Method, Result).
2.  **Introduction**: "Hourglass" structure (Broad -> Specific -> Method -> Impact).
3.  **Method**: Formal definition.
4.  **Experiments**: Strongman baselines + Ablation.
5.  **Compilation (Zero Warning Policy)**:
    - **Tool**: `skills/latex/scripts/latex_tool.py compile 04_manuscript/main.tex`
    - **Strict Check**:
      - **No "Overfull \hbox"**: Rewrite sentence or fix figure width.
      - **No "Undefined Citation"**: All `\cite{}` must resolve.
      - **No "Float too large"**: Resize images.
    - **Action**: Grep the `.log` file for `Warning`. Do not ignore them.

## Phase 4: Audit (ZeroGPT / Humanization Protocol)

### 1. Forbidden Words (The "AI-ese" Blacklist)

**Strict Rule**: `grep` for these words. If found, the paper is **NOT** ready.

- **Verbs**: `delve`, `showcase`, `underscore`, `highlight`, `leverage`, `foster`, `necessitate`.
- **Nouns**: `realm`, `tapestry`, `landscape`, `paradigm`, `nuance`, `synergy`.
- **Adjectives**: `burgeoning`, `pivotal`, `paramount`, `robust`, `comprehensive`, `intricate`.
- **Phrases**: "In conclusion", "As shown in", "It is worth noting that", "Recent years have witnessed".

### 2. Burstiness (Sentence Variance)

**Rule**: Never write 3 sentences of similar length in a row.

- **Mix**: Short (5 words) -> Long (25 words) -> Medium (15 words).
- **Rhythm**: "X is Y. However, because Z occurs, we find that W is true. Therefore, A implies B."

### 3. Voice (Opinionated)

- **Do not be neutral**: "We argue", "Surprisingly", "Contrary to [X]".
- **Use "We"**: Take ownership. "We hypothesize...", "We demonstrate...".

### 4. Structural Rules

- **Figure 1 Rule**: Must have a "teaser" figure on Page 1 (Top).

### 5. Bibliography Hygiene (Strict Mode)

- **Completeness**: `author`, `title`, `year`, `venue` required.
- **Capitalization**: Title Case for titles.
- **Preprint Policy**: Update ArXiv refs to published versions if >2 years old.

## Phase 5: The Nobel/Best Paper Standard (Elite Mode)

**Goal**: Aim for CVPR Best Paper / Nature / Nobel.

### 1. Theoretical Depth (The "Why")

- **Theorems**: Don't just show *it works*, prove *why*.
- **Scaling Laws**: Show performance as a function of compute/data (Power Laws).
- **First Principles**: Derive your method from physics/math, not just heuristics.

### 2. Generalization (The "Everywhere")

- **OOD Testing**: Test on unseen domains (e.g., train on Medical, test on Natural Images).
- **Cross-Modal**: Does it work for Audio/Video/Text?

### 3. Aesthetic Perfection

- **Figure 1**: Must be a masterpiece. Instantly conveys the core idea.
- **Notation**: Consistent, standard, and defined. No ambiguity.

## Summary Checklist (The "Golden Ticket")

- [ ] **Idea**: Novel (>30%), Feasible, Valued.
- [ ] **Data**: Broad Search -> Academic Check -> Repository.
- [ ] **Exp**: Main (L20) + Baselines (P100) + Ablations.
- [ ] **Run**: Smoke Test (Batch=2) -> Detached Exec -> Checkpoint (Best/Last).
- [ ] **Write**: Zero Warning LaTeX + ZeroGPT (No "Delve") + Figure 1 Masterpiece.
- [ ] **Elite**: Theoretical Proof + OOD Generalization.
