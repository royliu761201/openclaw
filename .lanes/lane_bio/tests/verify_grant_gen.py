
import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from skills.grant_writer import GrantWriter

async def main():
    print("Testing Grant Writer...")
    writer = GrantWriter()
    topic = "Quantum-Enhanced Transformer for Extreme Weather Prediction"
    context = "Climate models are too slow. We use quantum entangement in a Transformer to predict typhon paths 100x faster."
    guideline = "Total Budget: 100万元 (1 Million RMB). Project Duration: 4 Years. Focus on: 'Deep Learning', 'Climate Change', 'National Security'. Must show 'Preliminary Results'."
    
    zip_path = await writer.draft_proposal(topic, context, guideline)
    print(f"Generated: {zip_path}")
    
    if os.path.exists(zip_path):
        print("SUCCESS: Zip file exists.")
    else:
        print("FAILURE: Zip file missing.")

if __name__ == "__main__":
    asyncio.run(main())
