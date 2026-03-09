
import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from skills.patent_writer import PatentWriter

async def main():
    print("Testing Patent Writer...")
    writer = PatentWriter()
    topic = "Quantum-Enhanced Transformer for Biological Sequence Modeling"
    context = "We propose a novel Transformer architecture that uses quantum entanglement simulation to model long-range dependencies in DNA sequences. It achieves 99% accuracy."
    
    zip_path = await writer.draft_disclosure(topic, context)
    print(f"Generated: {zip_path}")
    
    if os.path.exists(zip_path):
        print("SUCCESS: Zip file exists.")
    else:
        print("FAILURE: Zip file missing.")

if __name__ == "__main__":
    asyncio.run(main())
