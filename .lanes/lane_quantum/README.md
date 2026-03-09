# ResearchBot (Nexus-AI4S)

ResearchBot is an autonomous scientific research system capable of conducting experiments, writing papers (LaTeX), drafting grants, and generating patents. It uses a Manager-Worker architecture with specialized agents.

## 📂 Project Structure

Verified 2026 Clean Architecture:

*   **`src/`**: Core source code (Flat Namespace).
    *   `agents/`: Specialized agents (PaperProducer, GrantWriter).
    *   `core/`: System orchestration (AgentTeam, DAG).
    *   `schemas/`: Data Models (Pydantic).
    *   `skills/`: Functional capabilities (Git, SSH, LaTeX, WebSearch).
    *   `ui/`: Dashboard application.
*   **`research_vault/`**: Long-term memory and assets.
    *   `library/`: Papers, Patents, Datasets.
    *   `templates/`: LaTeX templates (NeurIPS, NSFC, USPTO).
    *   `knowledge_base/`: Agent rules and profiles.
*   **`config/`**: System configuration.
*   **`tests/`**: Unit and integration tests.

## 🚀 Usage

### 1. Requirements
Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Running
This project is designed as a modular framework. You can import agents to build your own research loop:

```python
from src.core.graph_orchestrator import GraphOrchestrator

# Initialize and run
orchestrator = GraphOrchestrator(root_dir=".")
await orchestrator.run_cycle(topic="Your Research Topic")
```

### 3. Dashboard
Launch the Streamlit interface:
```bash
streamlit run src/ui/app.py
```

## 🛠 Configuration

System settings are located in `config/settings.yaml`.
You can override specific paper configurations by creating a local YAML file (see `config/paper_config_example.yaml`) and passing it to the runner.

## 🧪 Testing

Run unit tests:
```bash
pytest tests/
```
