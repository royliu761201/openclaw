import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.abspath("src"))

from core.optimization import AccelerationEngine

async def test_acceleration_engine():
    print("=== Testing AccelerationEngine ===")
    
    # 1. Test Visual Early Stopping (Mocked)
    print("\n[Test 1: Visual Early Stopping]")
    engine = AccelerationEngine()
    
    # Heuristic Stop (Loss Explosion)
    should_stop = await engine.check_early_stop({"loss": 5000}, 1, 100)
    assert should_stop == True
    print("✓ Detects loss explosion")
    
    # Visual Stop (Mocked random)
    # We loop a few times to catch the 5% chance, or just verify it runs without error
    print("Testing visual check (mocked probability)...")
    stops = 0
    for _ in range(50):
        if await engine.check_early_stop({"loss": 0.5}, 10, 100, curve_image_path="dummy.png"):
            stops += 1
    
    print(f"Visual check triggered {stops} times in 50 attempts (Expected small non-zero usually, but strictly >0 is chance based)")
    
    # 2. Test PrototypeFirst
    print("\n[Test 2: Prototype Derivation]")
    full_config = {
        "task_id": "transformer_train",
        "epochs": 200,
        "batch_size": 32,
        "model": "vit_large"
    }
    
    prototype = engine.prototype_first(full_config)
    
    print(f"Original Epochs: {full_config['epochs']}")
    print(f"Prototype Epochs: {prototype['epochs']}")
    assert prototype['epochs'] == 20 # 10% of 200
    assert prototype['use_proxy_data'] == True
    assert prototype['task_id'] == "transformer_train_proxy"
    print("✓ Prototype params derived correctly")

if __name__ == "__main__":
    asyncio.run(test_acceleration_engine())
