# Codebase Reflection (Feb 2026)

## 1. Directory Structure Status
We have successfully achieved a "Clean Root" architecture.

**Root Directory:**
*   Minimal: `src`, `scripts`, `config`, `tests`, `research_vault`, `data`.
*   Untracked Artifacts: `*_output`, `experiments`, `.kaggle_builds` are now strictly ignored.
*   Configuration: Consolidated in `config/` (removed root `config.yaml`).

**Source Code (`src/`):**
*   **Structure**: Flat layout (`src/core`, `src/agents`, `src/skills`).
*   **Observation**: There is NO `research_bot` parent package directory. `src` acts as the root namespace.
*   **Implication**: Imports are `from core.graph import...` rather than `from research_bot.core.graph import...`.
    *   *Pros*: Simpler imports for local development.
    *   *Cons*: Potential naming conflicts if installed as a library (e.g. `core` is very generic).
*   **Status**: Working correctly with `sys.path.append('src')` in entrypoints.

## 2. Git Hygiene
*   **Remote State**: We aggressively removed `scripts`, `.kaggle_builds`, and all `*_output` folders from the remote repository.
*   **Local State**: `scripts` remains locally for execution.
*   **Strategy**: The repository is now focused purely on the *application code* (`src`) and *knowledge* (`research_vault`). Execution scripts are treated as local tooling.

## 3. Next Steps
*   **Package namespace**: In the future, we might want to move `src/*` into `src/research_bot/*` to fully namespace the application, but this would require refactoring all imports.
*   **Docker**: Ensure `Dockerfile` (if it exists) updates `PYTHONPATH` to include `src`.
