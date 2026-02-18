# ResearchBot (Nexus-AI4S)

ResearchBot is an autonomous scientific research system capable of conducting experiments, writing papers (LaTeX), drafting grants, and generating patents. It uses a Manager-Worker architecture with specialized agents.

## 📂 Project Structure

Verified 2026 Clean Architecture:

- **`src/`**: Core source code (Flat Namespace).
  - `agents/`: Specialized agents (PaperProducer, GrantWriter).
  - `core/`: System orchestration (AgentTeam, DAG).
  - `schemas/`: Data Models (Pydantic).
  - `skills/`: Functional capabilities (Git, SSH, LaTeX, WebSearch).
  - `ui/`: Dashboard application.
- **`research_vault/`**: Long-term memory and assets.
  - `library/`: Papers, Patents, Datasets.
  - `templates/`: LaTeX templates (NeurIPS, NSFC, USPTO).
  - `knowledge_base/`: Agent rules and profiles.
- **`config/`**: System configuration.
- **`tests/`**: Unit and integration tests.

## 🚀 Usage

### 1. Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Environment Setup

To enable access to Gemini models, you must provide your Google API Key.
Recommended method: Point to your `secrets.json` file.

```bash
export SECRETS_FILE_PATH="/path/to/your/secrets.json"
```

The `secrets.json` should contain:

```json
{
  "GOOGLE_API_KEY": "your-api-key-here",
  "WANDB_API_KEY": "your-wandb-key",
  "remote": {
    "host": "your-remote-host",
    "port": 22,
    "user": "root",
    "pass": "your-password-optional",
    "key_path": "/path/to/private/key-optional"
  },
  "kaggle": {
    "username1": "api-key-1",
    "username2": "api-key-2"
  }
}
```

- **Kaggle**: Configure `"kaggle"` block in `secrets.json` for multi-account support.
- **Weights & Biases**: Set `WANDB_API_KEY` in `secrets.json`.
- **SSH**: Configure the `"remote"` block: `user` (required), `pass` OR `key_path` (for auth).

Alternatively, set the key directly:

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

### 3. Running

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
