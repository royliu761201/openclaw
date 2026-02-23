---
name: diagram-generator
description: Generate high-quality architecture diagrams, technical route maps, and systemic flowcharts as actual PNG/PDF files.
metadata:
  openclaw:
    requires:
      system: ["graphviz"]
---

# Diagram Generator Skill

This skill allows you (OpenClaw) to physically generate academic-grade diagrams (e.g., framework architecture, state machines, technical roadmaps) and save them as actual image files (`.png` or `.pdf`) to the user's workspace. Do not just output raw Mermaid or DOT code!

## Usage

When a user asks you to "draw an architecture diagram", "generate a technical route map", or "plot a flowchart":

1. **Design the Architecture**: Determine the components, layers, and data flow of the system requested.
2. **Translate to Graphviz (DOT)**: Write a strict, clean Graphviz `DOT` script representing the diagram. Use academic styles (e.g., strict rectangular nodes, clear directional edges, distinct subgraphs for logical layers).
3. **Execute the Renderer**: Use the `run_command` tool to execute the `render_architecture.py` script. Pass your DOT code snippet inside quotes. **Always save the output to the user's authorized workspace directory** (e.g., `/Users/roy-jd/Documents/projects/openclaw/workspace/route_map.png`).

```bash
# Example Execution
python skills/diagram-generator/render_architecture.py --output "/Users/roy-jd/Documents/projects/openclaw/workspace/llm_arch.png" --code 'digraph G { rankdir=LR; User -> API; API -> "LLM Engine"; "LLM Engine" -> Database; }'
```

4. **Return the File**: Once the rendering command completes without errors, provide the absolute path to the generated image file so the user can insert it straight into their paper or proposal.
