#!/usr/bin/env python3
"""
Lightweight import-smoke test.

By default:
- Tries packages named from pyproject [project.name] (hyphens -> underscores).
- Also auto-discovers top-level packages in ./src/* and ./*/ with __init__.py.
- You can override with: --packages pkg1,pkg2

Exit codes:
 0 = all good or nothing to test
 1 = at least one import failed
"""

from __future__ import annotations
import argparse
import importlib
import sys
import traceback
from pathlib import Path

def project_name_from_pyproject() -> list[str]:
    py = Path("pyproject.toml")
    names: list[str] = []
    if not py.exists():
        return names
    try:
        if sys.version_info >= (3, 11):
            import tomllib  # type: ignore
            data = tomllib.loads(py.read_text(encoding="utf-8"))
        else:
            import tomli as tomllib  # type: ignore
            data = tomllib.loads(py.read_text(encoding="utf-8"))
        name = (data.get("project") or {}).get("name")
        if isinstance(name, str):
            names.append(name.replace("-", "_"))
    except Exception:
        pass
    return names

def discover_packages() -> list[str]:
    candidates: set[str] = set(project_name_from_pyproject())

    # src layout
    src = Path("src")
    if src.is_dir():
        for p in src.iterdir():
            if (p / "__init__.py").exists() and p.is_dir():
                candidates.add(p.name)

    # flat layout (top-level dirs)
    for p in Path(".").iterdir():
        if p.is_dir() and (p / "__init__.py").exists() and not str(p).startswith((".git", "src", "scripts", ".")):
            candidates.add(p.name)

    # filter pythonic names
    return sorted({c for c in candidates if c.isidentifier()})

def try_import(mod: str) -> tuple[bool, str]:
    try:
        importlib.import_module(mod)
        return True, ""
    except Exception as e:
        tb = "".join(traceback.format_exception_only(type(e), e)).strip()
        return False, tb

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packages", help="Comma-separated module names to import", default="")
    args = ap.parse_args()

    if args.packages.strip():
        targets = [p.strip() for p in args.packages.split(",") if p.strip()]
    else:
        targets = discover_packages()

    if not targets:
        print("No Python packages discovered; skipping import smoke.")
        return 0

    print(f"Import smoke targets: {targets}")
    failed = 0
    for mod in targets:
        ok, err = try_import(mod)
        status = "OK" if ok else "FAIL"
        print(f"[{status}] import {mod}")
        if not ok:
            print(f"  Error: {err}")
            failed += 1

    if failed:
        print(f"{failed} import(s) failed.")
        return 1
    print("All imports succeeded.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
