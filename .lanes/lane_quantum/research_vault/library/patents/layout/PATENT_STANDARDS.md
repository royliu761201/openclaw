# AI4S High-Quality Patent Disclosure Standards

> **Core Principle**: A patent protects a **Technical Solution**, not an abstract idea.
> **Format**: STRICT LaTeX. Markdown drafts are for brainstorming only.

## 1. Document Format Standard
*   **Engine**: `xelatex` (Mandatory for Chinese character support).
*   **Package**: `ctex` (Do not use manual fontspec unless necessary).
*   **Structure**:
    1.  Front Matter (Title, Field)
    2.  Background & Technical Problem (Prior Art, Defect, Problem)
    3.  Technical Solution (Architecture, Modules, **Distinction**)
    4.  Beneficial Effects (Linked to Defects)
    5.  Embodiments (Benchmarks, Scenarios)
    6.  Claims Draft

## 2. Content Quality Checklist

### A. The "Three-Part" Logic (三性逻辑)
Your disclosure must form a logical loop:
1.  **Defect**: "Existing Prior Art X fails because of Y." (Be objective, strictly technical).
2.  **Solution**: "We introduce Module Z to fix Y." (Must be a technical means, not a wish).
3.  **Effect**: "Because of Z, performance improved by N%." (Must verify the fix).

### B. Mandatory "Distinction" Section
You **MUST** explicitly contrast your invention with:
*   **Rule-Based Systems**: Why is your AI approach better? (e.g., Generalization).
*   **Standard Deep Learning (SFT/RLHF)**: Why is your specific architecture better? (e.g., Logic Constraints, Decoupling, Training Stability).
    *   *Bad*: "Our model is better."
    *   *Good*: "Unlike SFT which minimizes sequence perplexity, our approach minimizes topological consistency loss via a differentiable projection layer."

### C. Terminology Rigor
*   **Do NOT use**: "Test-Time Training" (unless it actually is), "Thinking", "Understanding".
*   **DO use**: "Inference Phase", "Processing", "Mapping", "Optimizing".
*   **Projection**: If you use "Projector", define its mathematical basis (e.g., Manifold, Vector Space).

## 3. Workflow
1.  **Draft phase**: Iterate on logic.
2.  **Implementation phase**: Use `patents/templates/disclosure_template.tex`.
3.  **Review phase**: Compile to PDF. Check for "Mixed Markdown" and "Formatting Artifacts".

## 4. Forbidden Items
*   **Markdown Syntax in LaTeX**: No `**bold**`, use `\textbf{bold}`.
*   **Abstract Descriptions**: No "We hope to...", use "The system is configured to...".
*   **Internal Codes**: Remove internal project IDs or server names (e.g., "L20 Cluster", "Financial Logs" if irrelevant).
