#!/usr/bin/env python3
"""
Friendly smoke test for tools.yaml:
- Accepts either top-level list OR {'tools': [...]}
- Adds repo root (and optional ./src) to sys.path for local runs
- Imports each tool module
- Prints 'Imported: <key> (<module>) ✅' per success
- Exits 1 with clear messages if anything fails
"""

import importlib
import sys
from pathlib import Path

# Ensure repo root (and ./src) are on sys.path for local runs
REPO_ROOT = Path(__file__).resolve().parents[1]
for p in (REPO_ROOT, REPO_ROOT / "src"):
    if p.exists():
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)

try:
    import yaml  # PyYAML
except Exception:
    print("PyYAML missing. Run: pip install -r requirements.txt", file=sys.stderr)
    sys.exit(2)

TOOLS_FILE = REPO_ROOT / "tools.yaml"

def _load_entries():
    if not TOOLS_FILE.exists():
        raise FileNotFoundError(f"{TOOLS_FILE} not found in repo root")
    data = yaml.safe_load(TOOLS_FILE.read_text(encoding="utf-8")) or {}
    # Accept either {'tools': [...]} or just [...]
    if isinstance(data, dict) and "tools" in data:
        entries = data["tools"]
    elif isinstance(data, list):
        entries = data
    else:
        raise ValueError("tools.yaml must be a list or a mapping with top-level 'tools' key")
    if not isinstance(entries, list):
        raise TypeError("'tools' must be a list of tool entries")
    return entries

def main():
    entries = _load_entries()
    failures = []
    seen_keys = set()

    for i, entry in enumerate(entries, 1):
        key = entry.get("key")
        module = entry.get("module")
        label = entry.get("label", "")
        section = entry.get("section", "")

        if not key or not module:
            failures.append(f"[{i}] Missing key/module in entry: {entry!r}")
            continue
        if key in seen_keys:
            failures.append(f"[{i}] Duplicate key '{key}' in tools.yaml")
            continue
        seen_keys.add(key)

        try:
            importlib.import_module(module)
            print(f"Imported: {key} ({module}) ✅   [{label} | {section}]")
        except Exception as e:
            failures.append(f"[{i}] Failed to import {key} ({module}): {e}")

    if failures:
        print("\n--- Smoke Failures ---", file=sys.stderr)
        for f in failures:
            print(f, file=sys.stderr)
        sys.exit(1)

    print(f"\nAll {len(entries)} tool modules imported successfully ✅")
    return 0

if __name__ == "__main__":
    sys.exit(main())
