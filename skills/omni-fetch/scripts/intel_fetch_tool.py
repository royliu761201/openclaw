"""
Auto-Generated Entrypoint for intel-fetch
Enforces Sandbox Incarceration Law (L1 Constitution Rule 12)
"""
import sys
import os

# --- L1 SANDBOX INCARCERATION PROBE ---
in_venv = sys.prefix != sys.base_prefix
if not in_venv:
    print("⚠️ [L1 PROBE] Global scope detected. Self-incarcerating into VENV...")
    venv_python = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "venv/bin/python3")
    if not os.path.exists(venv_python):
        print("❌ Fatal: Sandbox VENV not found. Run Hermetic Drop deploy script first.")
        sys.exit(1)
    os.execv(venv_python, [venv_python] + sys.argv)
# ------------------------------------------

def main():
    print("[intel-fetch] Running securely inside VENV.")

if __name__ == "__main__":
    main()
