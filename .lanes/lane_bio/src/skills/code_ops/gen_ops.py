from typing import List, Optional

"""
Atomic Prompt Generation Operations for Code.
Pure functions that return prompt strings.
"""

def build_experiment_prompt(topic: str, context: str, framework: str = "pytorch") -> str:
    return f"""
    Role: Senior ML Engineer.
    Task: Write a COMPLETE, RUNNABLE Python script for: {topic}.
    Context: {context}
    
    Requirements:
    1. Framework: {framework} (or compatible).
    2. Structure:
       - Class-based Model definition.
       - `train()` loop with dummy data generation if real data unavailable.
       - `evaluate()` function.
       - `main()` block.
    3. I/O:
       - Save best model to 'model.pth'.
       - Save metrics to 'results.json' (CRITICAL).
       - Print readable logs.
       
    Constraint: Output Python Code ONLY. No markdown, no commentary.
    """

def build_viz_prompt(topic: str, context: str, output_filename: str) -> str:
    return f"""
    Role: Scientific Visualization Expert.
    Task: Write a Python script using Matplotlib to visualize: {topic}.
    Context: {context}
    
    Requirements:
    1. Style: Academic (Publication Quality), use 'seaborn-whitegrid' if possible.
    2. Data: Generate plausible dummy data representing the research outcome (e.g., 'Ours' > 'Baseline').
    3. Output: Save the figure to '{output_filename}'.
    
    Constraint: Output Python Code ONLY.
    """

def build_demo_prompt(topic: str, context: str) -> str:
    return f"""
    Role: Full Stack Prototype Engineer.
    Task: Write a single-file Streamlit app (`app.py`) to demonstrate: {topic}.
    Context: {context}
    
    Requirements:
    1. Interactive UI (Sliders, Input Text).
    2. Mock Inference (simulate the model output).
    3. Professional Layout.
    
    Constraint: Output Python Code ONLY.
    """

def build_optimize_prompt(code: str, objective: str) -> str:
    return f"""
    Role: Senior Software Architect.
    Task: Refactor and Optimize the following code.
    Objective: {objective.upper()} (e.g., Efficiency, Readability, PEP8, Security).
    
    Input Code:
    ```python
    {code}
    ```
    
    Requirements:
    1. Preserve exact functionality (unless logic is buggy).
    2. Improve based on the objective (e.g., use vectorization for efficiency).
    3. Add comments explaining the optimization.
    
    Constraint: Output Python Code ONLY.
    """
