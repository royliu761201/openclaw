import asyncio
import os
import sys

# Add project root and src to path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.core.llm_client import LLMClient
from src.agents.paper_producer import PaperProducer
from src.skills.git_executor import GitExecutor
from src.core.config_manager import ConfigManager

async def run():
    print("--- Regenerating Draft Sections ---")
    config_manager = ConfigManager()
    client = LLMClient() 
    git_manager = GitExecutor(os.getcwd()) 
    producer = PaperProducer(os.getcwd(), client, git_manager)
    
    # Paper Details
    slug = "micro_to_macro_physics_informed_neural_constitutiv"
    output_dir = os.path.join(os.getcwd(), "papers", slug)
    
    # Read Outline
    outline_path = os.path.join(output_dir, "outline_neurips_2026_(ai_for_science_track).md")
    if not os.path.exists(outline_path):
        print(f"Error: Outline not found at {outline_path}")
        return

    with open(outline_path, "r") as f:
        outline = f.read()

    # Config
    paper_config = {
        "title": "Micro-to-Macro: Physics-Informed Neural Constitutive Discovery for High-Strain Rate Explosion Simulation",
        "venue": "NeurIPS 2026"
    }
    
    # Write only previously corrupted sections
    # Write only previously corrupted sections
    targets = ["Introduction", "Related Work"]
    
    # Also Regenerate Abstract (User reported issues + I deleted it)
    print("re-generating abstract...")
    abstract_content = await producer._generate_abstract(paper_config["title"], outline)
    with open(os.path.join(output_dir, "sections/00_abstract.tex"), "w") as f:
        f.write(abstract_content)
        
    # Generate Bibliography (Critical for citations)
    bib_path = os.path.join(output_dir, "refs.bib")
    if not os.path.exists(bib_path):
        print("Creating fresh bibliography...")
        # Use a generic context for bib generation if specific context isn't handy, 
        # or use the outline as context which contains key citations hints.
        await producer._generate_bibliography(paper_config["title"], outline, output_dir)
        
    await producer.write_draft(paper_config, outline, output_dir, target_sections=targets)
    print("--- Done ---")

if __name__ == "__main__":
    asyncio.run(run())
