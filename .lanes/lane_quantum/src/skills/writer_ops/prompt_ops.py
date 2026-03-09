from typing import Union, List

"""
Atomic Prompt Operations.
Pure functions to construct prompts for research writing tasks.
"""

def construct_multimodal_prompt(instruction: str, context: Union[str, List[any]]) -> Union[str, List[any]]:
    """Helper for text/multimodal prompt construction."""
    if isinstance(context, list):
        return [instruction] + context
    else:
        return f"{instruction}\n\nContext:\n{context}"

def build_critique_prompt(reviewer_persona: str, section: str, criteria: str, content: str) -> str:
    return f"""
    Role: {reviewer_persona}
    Task: Critique the following section ('{section}').
    
    Criteria:
    {criteria}
    
    Content:
    {content}
    
    Output: "PASS" or a list of fatal defects.
    """

def build_refine_prompt(drafter_persona: str, critique: str, content: str) -> str:
    return f"""
    Role: {drafter_persona}
    Task: Rewrite section based on Critique.
    
    Critique: 
    {critique}
    
    Original Content: 
    {content}
    
    Instruction: Return FULLY REWRITTEN LaTeX content.
    """

def build_application_prompt(mode: str, topic: str, context: str) -> str:
    """Constructs prompt for Practical Application section based on mode."""
    if "Patent" in mode:
        return f"""
        Role: Senior Patent Attorney.
        Task: Describe a 'Preferred Embodiment' (实施例) for: {topic}.
        Context: {context}
        
        Requirement:
        - **Hardware/Software Integration**: "The system comprises Module A connected to..."
        - **Step-by-Step Operation**: "In Step S101..."
        - **Technical Advantage**: Compare vs Prior Art.
        
        Output: LaTeX formatted subsection.
        """
    elif "Grant" in mode:
        return f"""
        Role: Strategic Policy Analyst.
        Task: Describe the 'Social & Economic Impact' for: {topic}.
        Context: {context}
        
        Requirements:
        - **National Strategy Alignment**: Cite "14th Five-Year Plan".
        - **Economic Value**: "Projected cost reduction..."
        - **SWOT Analysis**.
        
        Output: LaTeX formatted subsection.
        """
    else: # Paper
        return f"""
        Role: Senior Scientist.
        Task: Describe a 'Real-World Case Study' deployment for: {topic}.
        Context: {context}
        
        Requirements:
        - **Scenario**: "Deployed in Hospital X..."
        - **Comparison**: "Outperformed experts..."
        - **Critical Analysis** (Pros/Cons).
        
        Output: LaTeX formatted subsection.
        """

def build_demo_code_prompt(topic: str, context: str) -> str:
    return f"""
    Role: Senior Data Scientist.
    Task: Create a 'demo_app.py' (Streamlit) to SIMULATE: {topic}.
    Context: {context}
    
    Requirements:
    1. **Simulation Logic**: Synthetic data processing.
    2. **Visuals**: Plot results.
    3. **Interactivity**: Sliders for hyperparameters.
    4. **Clean Code**: No markdown, standard imports.
    
    Output: Python Code ONLY.
    """
