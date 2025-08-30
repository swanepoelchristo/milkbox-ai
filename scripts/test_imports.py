import importlib
import os
import sys

# Ensure repo root and streamlit_app are on sys.path
REPO_ROOT = os.path.abspath(os.path.dirname(__file__) + "/../../")
STREAMLIT_APP = os.path.join(REPO_ROOT, "streamlit_app")
for p in [REPO_ROOT, STREAMLIT_APP]:
    if p not in sys.path:
        sys.path.insert(0, p)

modules = [
    "tools.hello",
    "tools.notes",
    "tools.invoice_gen",
    "tools.bar_tools",
    "tools.cv_builder",
    "tools.cv_builder_pro",
    "tools.demo_2",
    "tools.builder",
    "tools.food_safety",
]

print("=== Import smoke ===")
failures = []
for m in modules:
    try:
        importlib.import_module(m)
        print(f"  ✔ {m}")
    except Exception as e:
        print(f"  ✖ {m} -> {e}")
        failures.append(m)

if failures:
    print("\nImport errors detected:")
    for m in failures:
        print(" -", m)
    sys.exit(1)

print("All tool modules imported successfully.")
