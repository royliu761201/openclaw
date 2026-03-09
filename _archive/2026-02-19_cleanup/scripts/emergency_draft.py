import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.core.llm_client import LLMClient
from src.core.config import ModelTier

async def emergency_draft():
    client = LLMClient()
    
    # Ensure client is initialized (helper check)
    if not client.client:
        print("Failed to init genai client. Check API Key.")
        return

    output_dir = "grant_output/emergency"
    os.makedirs(output_dir, exist_ok=True)
    
    topic = "Physics-Informed Generative AI with Manifold Constraints for Complex Material Design"
    
    # Prompts (Option A)
    prompts = {
        "nsfc_1_1.tex": f"""
            Role: Academic Grant Writer (NSFC).
            Topic: {topic}
            Section: 1. 本项目的研究内容、项目开展的必要性及与重大研究计划总体科学目标的关系。
            Requirements:
            - Write in refined Chinese.
            - Approx 800 words.
            - Focus on "Manifold Constraints" and "Generative Modeling".
            - Format: LaTeX text only (no preamble).
        """,
        "nsfc_1_2.tex": f"""
            Role: Academic Grant Writer (NSFC).
            Topic: {topic}
            Section: 2. 本项目拟解决的关键科学问题、拟采取的研究方案及可行性分析。
            Requirements:
            - Write in refined Chinese.
            - Key Question 1: How to embed conservation laws into latent space?
            - Key Question 2: "Dual Helix" optimization convergence.
            - Scheme: Generative foundation model + PINNs.
            - Format: LaTeX text only (with \\subsection* if needed).
        """,
        "nsfc_1_3.tex": f"""
            Role: Academic Grant Writer (NSFC).
            Topic: {topic}
            Section: 3. 年度研究计划及预期研究成果。
            Requirements:
            - Timeline: 2027-2029 (3 Years).
            - Deliverables: 5 Papers, 1 Open Source Codebase.
            - Format: LaTeX text only.
        """,
        "nsfc_2_1.tex": f"""
            Role: Academic Grant Writer (NSFC).
            Topic: {topic}
            Section: (二) 研究基础
            Requirements:
            - Mention previous work on "Micro-to-Macro PINNs".
            - Mention "Constitutive Discovery" success.
            - Format: LaTeX text only.
        """
    }
    
    print(f"Drafting Emergency Proposal for: {topic}")
    
    for filename, mk_prompt in prompts.items():
        print(f"Generating {filename}...")
        # Use string alias to force stability if Enum fails in deep logic, 
        # but my patch handles ModelTier.CRITICAL -> gemini-2.0-flash-exp
        # I'll use the direct string "gemini-2.0-flash-exp" to be 100% sure.
        try:
            content = await client.chat(mk_prompt, tier="gemini-2.0-flash-exp")
            with open(os.path.join(output_dir, filename), "w") as f:
                f.write(content)
            print(f"Saved {filename} ({len(content)} chars)")
        except Exception as e:
            print(f"Failed {filename}: {e}")
            # Fallback text
            with open(os.path.join(output_dir, filename), "w") as f:
                f.write(f"% Generation Failed for {filename}: {e}")

if __name__ == "__main__":
    asyncio.run(emergency_draft())
