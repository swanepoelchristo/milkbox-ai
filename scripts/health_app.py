from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "streamlit_app"

if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

def main():
    __import__("app")  # import the Streamlit app to catch top-level errors
    import scripts.smoke_tools as smoke
    smoke.main()
    print("HEALTHY: app imported and smoke test passed.")

if __name__ == "__main__":
    main()
