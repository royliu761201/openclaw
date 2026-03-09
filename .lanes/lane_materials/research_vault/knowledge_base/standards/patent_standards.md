# Standards for High-Quality Patent Disclosures (CNIPA)

## Core Philosophy: "A Problem, A Solution, A Result"
A patent is not a paper. It does not care about "Novelty of Theory" but "Novelty of TECHNICAL MEANS".

## 1. Five Elements of a Perfect Disclosure
1.  **Technical Problem (技术问题)**: Must be objective.
    *   *Bad*: "Existing AI is dumb."
    *   *Good*: "Existing Transformer attention mechanisms have O(N^2) complexity, causing high latency on edge devices (Specific Deficiency)."
2.  **Technical Solution (技术方案)**: The "How" (Core).
    *   **Clear, Complete, Accurate**: Must enable a "Person Skilled in the Art" to reproduce it.
    *   **Structure**: Hardware (Parts & Connections) or Software (Steps & Parameters).
    *   *Bad*: "We use a smart algorithm to optimize speed."
    *   *Good*: "A sparse attention block that selects Top-K tokens based on query-key dot products before softmax."
3.  **Beneficial Effects (有益效果)**: The "Why" (Data-Driven).
    *   Must compare directly with the Prior Art cited in Background.
    *   *Good*: "Reduces memory footprint by 40% compared to standard BERT (Data Support)."
4.  **Embodiments (实施例)**: The "Proof".
    *   At least **2-3 variations**. (e.g., Applied to NLP, Applied to Vision, Hardware considerations).
    *   **Must be Concrete**: Specific values, specific materials.
5.  **Claims (权利要求)**: The "Fence".
    *   **Claim 1 (Independent)**: Broadest possible protection. Minimal necessary traits.
    *   **Dependent Claims**: Fallback positions with specific parameters.

## 2. The Logic Triangle (The "Golden Standard")
A good disclosure must perfectly align these three:
*   **Problem**: What is wrong with the old way?
*   **Solution**: What specific step fixes that exact wrong thing?
*   **Effect**: What data proves that specific wrong thing is fixed?

## 3. Common Pitfalls (Why Patents Fail)
*   **Abstract Idea**: "A method for happier users" (Cannot patent mental concepts).
*   **Marketing Language**: "Best", "Revolutionary", "Perfect". (Forbidden).
*   **Lack of Support**: Claiming "for all devices" but only describing a GPU implementation.

## 4. The "Paper to Patent" Shift
| Academic Paper | Patent Disclosure |
| :--- | :--- |
| Focus: "Why it works" (Theory) | Focus: "How to build it" (Steps) |
| Goal: Spread Knowledge | Goal: Define Property Rights |
| Style: Persuasive, Narrative | Style: Dry, Repetitive, Precise |
| Figures: Performance Plots | Figures: System Flowcharts, Block Diagrams |
