import importlib
import yaml
from pathlib import Path

TOOLS_FILE = Path(__file__).parent.parent / "streamlit_app" / "tools.yaml"

def load_tools():
    with open(TOOLS_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("tools", [])

def test_imports():
    tools = load_tools()
    print("🔎 Running tool import smoke test...\n")

    for tool in tools:
        key = tool.get("key")
        module = tool.get("module")

        try:
            importlib.import_module(module)
            print(f"✅ {key} → {module} imported successfully")
        except Exception as e:
            print(f"❌ {key} → {module} FAILED")
            print(f"   Error: {e}")

if __name__ == "__main__":
    test_imports()
