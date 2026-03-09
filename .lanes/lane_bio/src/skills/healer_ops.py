from typing import Optional, List, Tuple
import re

async def heal_content(model_client, 
                      content: str, 
                      error_log: str, 
                      file_type: str = "text", 
                      context: str = "") -> Optional[str]:
    """
    Atomic Op: Uses LLM to fix broken content based on error logs.
    """
    if not model_client:
        print("[HealerOps] ⚠️ No ModelClient provided.")
        return None

    log_snippet = error_log[-4000:]
    
    prompt = f"""
    You are an expert {file_type} Debugger.
    Fix the following content based on the error log.
    
    Error Log (Snippet):
    ...
    {log_snippet}
    ...
    
    Broken Content:
    {content}
    
    Context: {context}
    
    Task:
    1. Identify the syntax error or logical failure.
    2. Fix it directly.
    3. Return RAW content only (No markdown blocks).
    """
    
    print(f"[HealerOps] 🚑 Healing {file_type} content...")
    try:
        from config import ModelTier
        new_content = await model_client.chat(
            prompt, 
            tier=ModelTier.STANDARD, 
            task_type="coding", 
            system_instruction=f"You are a silent {file_type} repair engine. Output only valid source code."
        )
        
        # Cleanup
        new_content = new_content.replace(f"```{file_type}", "").replace("```", "").strip()
        return new_content
        
    except Exception as e:
        print(f"[HealerOps] ❌ Healing Failed: {e}")
        return None

async def diagnose_execution_error(model_client,
                                 context_name: str, 
                                 error_log: str, 
                                 broken_content: str = "") -> List[Tuple[str, str]]:
    """
    Atomic Op: Diagnoses runtime errors and prescribes shell/code actions.
    """
    if not model_client:
        return []

    prompt = f"""
    [CRITICAL SYSTEM ERROR]
    Context: {context_name}
    
    BROKEN CONTENT:
    ```
    {broken_content[:2000]} 
    ```
    
    ERROR TRACEBACK:
    {error_log[-4000:]}
    
    TASK:
    Analyze error and provide fix actions.
    - If MISSING DEPENDENCY: Provide ```bash ... ```
    - If CODE ERROR: Provide ```python ... ``` with FIXED code.
    - If SYSTEM ERROR: Provide ```bash ... ```
    """
    
    from config import ModelTier
    response = await model_client.chat(
        prompt, 
        tier=ModelTier.CRITICAL, 
        task_type="debugging"
    )
    
    actions = []
    # robust regex parsing
    shell_blocks = re.findall(r"```bash(.*?)```", response, re.DOTALL)
    for block in shell_blocks: actions.append(("shell", block.strip()))
    
    code_blocks = re.findall(r"```python(.*?)```", response, re.DOTALL)
    for block in code_blocks: actions.append(("code", block.strip()))
    
    return actions
