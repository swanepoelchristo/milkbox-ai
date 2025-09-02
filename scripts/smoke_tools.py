#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import importlib
from pathlib import Path

import yaml  # requires PyYAML

# Paths
ROOT = Path(__file__).resolve().parents[1]      # repo root
APP = ROOT / "streamlit_app"                    # streamlit app folder
TOOLS_FILE = ROOT / "tools.yaml"                # tools manifest

# Make "tools.*" importable (streamlit_app on sys.path)
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))


def load_tools() -> list[dict]:
    """Read tools.yaml and return the list of tools."""
    data = yaml.safe_load(TOOLS_FILE.read_text(encoding="utf-8")) or {}
    tools = data.get("tools", []) or []
    # normalize; keep only items with key+module
    out = []
    for t in tools:
        if isinstance(t, dict) and t.get("key") and t.get("module"):
            out.append(
                {
                    "key": str(t["key"]).strip(),
                    "module": str(t["module"]).strip(),
                }
            )
    return out


def apply_filter(tools: list[dict]) -> list[dict]:
    """
    If TOOLS_FILTER is set to a comma list of keys ("hello,notes"),
    keep only those; otherwise return all.
    """
    raw = os.getenv("TOOLS_FILTER", "").strip()
    if not raw:
        return tools
    wanted = {x.strip() for x in raw.split(",") if x.strip()}
    return [t for t in tools if t["key"] in wanted]


def main() -> int:
    tools = apply_filter(load_tools())
    if not tools:
        print("No tools to test (TOOLS_FILTER produced empty set).")
        return 0

    failed = 0
    for t in tools:
        key = t["key"]
        modname = t["module"]
        try:
            m = importlib.import_module(modname)
            if not hasattr(m, "render"):
                raise RuntimeError("module has no render()")
            print(f"OK  {key:10}  {modname}")
        except Exception as e:
            print(f"BAD {key:10}  {modname} -> {e}")
            failed += 1

    if failed:
        print(f"\nFAILED tools: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
