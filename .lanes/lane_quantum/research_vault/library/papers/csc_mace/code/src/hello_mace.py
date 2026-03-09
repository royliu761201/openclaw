
import torch
import ase
from mace.calculators import MACECalculator

def main():
    print("🚀 MACE Hello World")
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Device: {torch.cuda.get_device_name(0)}")

    # Initialize Calculator (pretrained default)
    # This will trigger download of a small default model if not present
    try:
        calc = MACECalculator(model="medium", device="cuda")
        print("✅ MACE Calculator initialized successfully (medium model)")
    except Exception as e:
        print(f"⚠️ Failed to init default model (might need explicit path): {e}")

if __name__ == "__main__":
    main()
