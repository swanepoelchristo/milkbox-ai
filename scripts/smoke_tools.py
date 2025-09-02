#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
import importlib
import importlib.util
from pathlib import Path
import yaml  # PyYAML

ROOT = Path(__file__).resolve().parents[1]       # repo root
APP = ROOT / "streamlit_app"
TOOLS_FILE = ROOT / "tools.yaml"

# Ensure "tools.*" under streamlit_app is importable
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))


def load_tools() -> list[dict]:
    data = yaml.safe_load(TOOLS_FILE.read_text(encoding="utf-8")) or {}
    items = data.get("tools", []) or []
    out: list[dict] = []
    for t in items:
        if isinstance(t, dict) and t.get("key") and t.get("module"):
            out.append({"key": str(t["key"]).strip(), "module": str(t["module"]).strip()})
    return out


def apply_filter(items: list[dict]) -> list[dict]:
    raw = os.getenv("TOOLS_FILTER", "").strip()
    if not raw:
        return items
    wanted = {x.strip() for x in raw.split(",") if x.strip()}
    return [t for t in items if t["key"] in wanted]


def import_with_fallback(modname: str, key: str):
    """
    Try importlib.import_module(modname) first.
    If that fails (e.g. No module named 'tools.notes'), try to load
    streamlit_app/tools/<key>.py by path, aliasing it to 'modname'.
    """
    try:
        return importlib.import_module(modname)
    except ModuleNotFoundError:
        candidate = APP / "tools" / f"{key}.py"
        if candidate.exists():
            spec = importlib.util.spec_from_file_location(modname, str(candidate))
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[modname] = mod
                spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                return mod
        # Re-raise if we couldn’t fall back
        raise


def main() -> int:
    items = apply_filter(load_tools())
    if not items:
        print("No tools to test (empty set after TOOLS_FILTER).")
        return 0

    failed = 0
    for t in items:
        key, modname = t["key"], t["module"]
        try:
            mod = import_with_fallback(modname, key)
            if not hasattr(mod, "render"):
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
