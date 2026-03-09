# Scientific Taste: Citation Policy

## 1. Authority (The Classics)
- **Authority**: Must cite foundational papers (e.g., Friston 2010 for FEP, Vaswani 2017 for Transformers, Sutton 2018 for RL).
- **Recency**: **CRITICAL**: At least **50%** of references must be from the last 3 years (e.g., 2024, 2025, 2026).
- **Volume**: A standard conference paper must contain at least **35 references**.
- **Diversity**: Do not over-cite a single lab or author. Ensure coverage of SOTA baselines.

## 5. Density & Balance
- **Golden Rule**: Cite 1-2 papers per major unique claim. 
- **Avoid "Citation Dumping"**: Do NOT list more than 3 citations in a single bracket (e.g., avoid `[1, 2, 3, 4, 5]`). Instead, cite the most authoritative review + the original paper.
- **Not Too Sparse**: Every technical assertion (e.g., "RL suffers from high variance") MUST be grounded by a citation.
- **Not Too Dense**: Do not interrupt every sentence with a citation; group them logically at the end of clauses.
- Science moves fast. Ignoring recent work makes your research obsolete before it starts.
- **Action**: Use `search_client` to find "survey [topic] 2024" or "state of the art [topic]".

## 3. Diversity (Anti-Bias)
- Do not cite papers from only one lab or company.
- Look for diverse approaches (e.g., if you are doing Deep Learning, also check if there are Symbolic AI or Bayesian approaches to the same problem).

## 4. Relevance
- Do not "citation dump". Only cite what you actually read or use.
- Connect the citation: "Unlike [Author, Year] who used X, we use Y because..."
