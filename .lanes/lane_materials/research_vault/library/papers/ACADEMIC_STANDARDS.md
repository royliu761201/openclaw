# 🎓 AI4S Academic Standards & Best Practices

**Objective**: To produce papers that are not just "accepted", but **best paper candidates**.

This document codifies the "Gold Standard" for all AI4S manuscripts. The `paper_automation.py` script enforces these rules.

---

## 1. ✒️ LaTeX Typography & Formatting
*   **Smart Quotes**: NEVER use straight quotes (`"`).
    *   ❌ Wrong: `"MedTime" is robust.`
    *   ✅ Right:   ``` ``MedTime'' is robust. ```
*   **Markdown Artifacts**: LaTeX is not Markdown.
    *   ❌ Wrong: `**Accuracy**`, `_Score_`
    *   ✅ Right: `\textbf{Accuracy}`, `\textit{Score}`
*   **Non-Breaking Spaces** (`~`): Essential for professional typesetting.
    *   **Rule**: Always use `~` before number references, citations, and units.
    *   ❌ Wrong: `Figure \ref{fig:1}`, `Table \ref{tab:3}`, `in \cite{vaswani}`
    *   ✅ Right: `Figure~\ref{fig:1}`, `Table~\ref{tab:3}`, `in~\cite{vaswani}`
*   **Math Mode**: Variables must be in math mode.
    *   ❌ Wrong: `where x is the input`
    *   ✅ Right: `where $x$ is the input`

## 2. 📚 Citations & Bibliography
*   **No Preprints for Published Work**: If a paper is accepted to CVPR/ICCV/ACL/NeurIPS, you **MUST** cite the formal venue, not the arXiv version.
    *   *The Automation Script will scan for `journal={arXiv}` and flag it if the paper is >6 months old.*
*   **Protection**: Protect acronyms in titles to preserve capitalization.
    *   ❌ Wrong: `title={Learning representations for nlp}`
    *   ✅ Right: `title={Learning Representations for {NLP}}`

## 3. 🤖 AI Integrity (GPTZero)
*   **Human-First Writing**: The Abstract and Introduction must be primarily human-written to ensure logical flow and avoid "AIese" (e.g., "delves into", "comprehensive framework").
*   **AI Detection**: We target a **GPTZero Score < 10%**.
    *   *Self-Check*: Use the pipeline to scan for commonly flagged AI phrases.

## 4. 🖼️ Figures & Visuals
*   **Vector First**: Use `.pdf` or `.eps` for all charts/diagrams.
*   **High-Res Raster**: If using `.png` (for screenshots/renders), specific DPI > 300.
*   **Font Consistency**: Text in figures should match the caption font size (approx. 8-10pt).
*   **Color Blindness**: Use palettes like Seaborn `colorblind` or Viridis.

---

## 5. 🏗️ Structural Completeness (The "Full Stack" Paper)
A high-level paper must contain the following distinct components (checked by `paper_automation.py`):
*   **Abstract & Intro**: Must clearly state the "Innovation" (Innovation Point).
*   **Methodology**: Must include a **Theoretical Analysis** subsection (not just architecture diagrams).
*   **Experiments**:
    *   **Main Results**: Comparison with SOTA.
    *   **Ablation Study**: Prove *every* proposed component contributes value.
    *   **Limitations**: Honest discussion of failure cases (do not hide them).

## 6. 🔬 Scientific Rigor
*   **Recent Baselines**: "Straw Man" baselines are grounded for rejection. You must compare against SOTA from the **last 2 years**.
    *   *Audit*: The automation script now checks if >30% of citations are from [Current Year - 2] onwards.
## 7. 🔄 Reproducibility (The "Gold Standard")
*   **Code Availability**: The paper MUST point to a GitHub repo (or promise release).
    *   *Audit*: Checks for "GitHub", "source code", or "available at".
*   **Deterministic Experiments**:
    *   Must explicitly state the **Random Seeds** used (e.g., "Seeds 42, 123, 2024").
    *   State hardware details (e.g., "NVIDIA L20").
*   **Statistical Significance**: Results should report Mean $\pm$ Std Dev over at least 3 runs.

## 8. 🧠 Innovation Consistency (The "Soul")
*   **The Golden Thread**: The article must revolve around **ONE** core innovation. Do not scatter focus.
*   **Terminology**: Define your method's name ONCE (e.g., "MedTime") and use it consistently.
    *   ❌ Inconsistent: "Our method", "The framework", "Proposed model".
    *   ✅ Consistent: "MedTime", "The proposed MedTime".

## 9. 📏 Length & Content Density
*   **Maximize Space**: Conference papers (CCF-A) should define the "state of the art" and thus require space.
*   **Target Length**: Close to the maximum allowed (e.g., 8 pages).
    *   *Metric*: Target **> 6000 words**. If it's short, you are likely missing details or ablation studies.

## 10. 📖 Bibliography Integrity
*   **Quantity**: A strong paper stands on the shoulders of giants.
    *   **Minimum**: 30 References.
    *   **Target**: **40 References**.
*   **Validity**: ABSOLUTELY NO HALLUCINATED CITATIONS.
    *   Every citation must be verifiable (DOI/Link).
    *   *Audit*: The pipeline checks for count and basic formatting validity.

## 11. 🎨 Visual Excellence & Layout
*   **Format**: Use **Vector Graphics** (PDF/SVG) for all plots.
    *   ❌ Avoid: PNG/JPG (unless for photos). Pixelation is unacceptable.
*   **Information Density**: Figures must be rich. No "toy examples".
*   **Compact Layout**:
    *   Whitespace is expensive. Minimize it.
    *   Use `\vspace{-0.2cm}` to tighten figure captions if necessary.
    *   **Audit**: Checks for low-res raster images and excessive whitespace.

## 12. 🎭 Narrative & Reviewer Perspective
*   **The Story ("娓娓道来")**:
    *   Do not just list experiments. **Tell a journey.**
    *   *Structure*: Challenge $\rightarrow$ Insight $\rightarrow$ Method $\rightarrow$ Verification $\rightarrow$ Conclusion.
    *   transitions must be smooth. "To address X, we propose Y. However, Y fails at Z, so we introduce Q."
*   **The Reviewer's Lens**:
    *   **Innovation**: Is it a "Delta" or a "Novelty"? (We want Delta).
    *   **Solid Verification**:
        *   Did you attack your own method? (Ablation).
        *   Did you fail? (Honest Limitations).
        *   Is the gain from the *core innovation* or just hyperparameter tuning?
*   **The Reviewer Checklist**:
    1.  **Novelty**: Does the Abstract kill the "So What?" question immediately?
    2.  **Solidity**: Are the baselines weak (Strawman)? If yes, REJECT.
    3.  **Flow**: Did I have to re-read a paragraph to understand? If yes, REWRITE.

## 13. 📊 Data Strategy: The "Fuel"
*   **Public Datasets**: You MUST exhaustively search for public benchmarks (MIMIC, Kaggle, HuggingFace). Use at least 2 public datasets to prove generalization.
*   **Private/Simulation Data**:
    *   **Necessity**: To prove your method handles edge cases, you MUST construct a controlled private or **Simulation Dataset**.
    *   *Why*: Simulation allows perfect ground truth and stress testing (Ablation).
    *   *Audit*: Check for "Simulation" or "Synthetic" or "Private collection" in the Experiment section.

## 14. 🛡️ Resilience & Project Context
*   **Paper $\in$ Project**: A paper is just a *snapshot* of a Project.
    *   Experiments MUST run in the **Project Environment**, accessing shared libs (`src/`).
    *   Do NOT isolate code in `papers/xxx/code` without linking to the main `src/` repo.
*   **Failure Resilience ("挺住")**:
    *   **Data Fails**: If data download fails, mock it or simulate it. Do NOT crash.
    *   **Env Fails**: If CUDA OOMs, reduce batch size and retry. Do NOT crash.
    *   **Logic Fails**: If accuracy is 0.0, check labels. Do NOT pivot method yet.

## 15. 🌟 Serendipity: The "Spark"
*   **Unexpected Results**: If an experiment fails in a weird way (e.g., accuracy spikes then drops), this is a **Discovery**, not just a bug.
*   **Capture It**: You MUST document these "Sparks" in the `Future Work` section or a dedicated note.
*   **Branching**: A "Spark" should trigger a NEW research proposal for the Agent to explore later.








