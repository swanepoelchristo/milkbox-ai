import importlib
import yaml
from pathlib import Path

TOOLS_YAML = Path(__file__).resolve().parent.parent / "tools.yaml"

def load_tools():
    with open(TOOLS_YAML, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["tools"]

def run_import_tests():
    tools = load_tools()
    print("🔍 Running tool import smoke test...\n")
    failed = []
    for tool in tools:
        key = tool["key"]
        module_path = tool["module"]
        try:
            importlib.import_module(module_path)
            print(f"✅ {key} → {module_path} OK")
        except Exception as e:
            print(f"❌ {key} → {module_path} FAILED: {e}")
            failed.append((key, str(e)))
    print("\n---\n")
    if failed:
        print("⚠️ Import errors detected:")
        for key, err in failed:
            print(f"   - {key}: {err}")
        exit(1)
    else:
        print("🎉 All tools imported successfully!")

if __name__ == "__main__":
    run_import_tests()
