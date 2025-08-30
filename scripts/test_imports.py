#!/usr/bin/env python3
"""
Tidy import smoke for milkbox-ai.

What it imports (in this order):
  1) `streamlit_app` if it exists (package folder OR single .py file at root or under src/)
  2) Every real package under src/*

Key fix:
  - Force the REPO ROOT onto sys.path even though this script runs from scripts/.

CLI:
  --packages "pkg1,pkg2"  -> force exact modules
  --allow-empty           -> exit 0 if nothing to test
Exit codes: 0 ok (or nothing w/ --allow-empty), 1 if any import fails
"""
from __future__ import annotations
import argparse, importlib, importlib.util, sys, traceback
from pathlib import Path
from typing import List, Tuple, Optional

def ensure_repo_root_on_path() -> None:
    # script is .../repo/scripts/test_imports.py -> repo root is parents[1]
    repo_root = Path(__file__).resolve().parents[1]
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)

def ensure_src_on_path() -> None:
    src = Path("src")
    if src.is_dir():
        sys.path.insert(0, str(src.resolve()))

def have_streamlit_app() -> tuple[Optional[str], Optional[Path]]:
    # package folder?
    if (Path("streamlit_app") / "__init__.py").exists():
        return "streamlit_app", None
    if (Path("src") / "streamlit_app" / "__init__.py").exists():
        return "streamlit_app", None
    # single files
    for p in [Path("streamlit_app.py"), Path("src/streamlit_app.py")]:
        if p.exists():
            return "streamlit_app", p
    return None, None

def src_packages() -> List[str]:
    out: List[str] = []
    src = Path("src")
    if src.is_dir():
        for p in src.iterdir():
            if p.is_dir() and (p / "__init__.py").exists() and p.name.isidentifier():
                out.append(p.name)
    return sorted(set(out))

def import_module(name: str) -> tuple[bool, str]:
    try:
        importlib.import_module(name)
        return True, ""
    except Exception as e:
        return False, "".join(traceback.format_exception_only(type(e), e)).strip()

def import_file(path: Path, alias: str) -> tuple[bool, str]:
    try:
        spec = importlib.util.spec_from_file_location(alias, str(path))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            sys.modules[alias] = mod
            return True, ""
        return False, f"Unable to load spec for {path}"
    except Exception as e:
        return False, f"{path}: " + "".join(traceback.format_exception_only(type(e), e)).strip()

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packages", default="")
    ap.add_argument("--allow-empty", action="store_true")
    args = ap.parse_args()

    # 🔧 critical: make repo root and src importable
    ensure_repo_root_on_path()
    ensure_src_on_path()

    forced = [x.strip() for x in args.packages.split(",") if x.strip()]
    targets: List[tuple[str, Optional[Path]]] = []

    if forced:
        targets = [(name, None) for name in forced]
    else:
        name, path = have_streamlit_app()
        if name:
            targets.append((name, path))
        for pkg in src_packages():
            if pkg != "streamlit_app":
                targets.append((pkg, None))

    print(f"PYTHONPATH head: {sys.path[:4]}")
    print("Smoke targets:", [t[0] + ("" if t[1] is None else f' (file:{t[1]})') for t in targets])

    if not targets:
        if args.allow_empty:
            print("Nothing to test (allow-empty)."); return 0
        print("No targets found."); return 1

    failed = 0
    for idx, (name, file_path) in enumerate(targets, 1):
        if file_path is None:
            ok, err = import_module(name)
            print(f"[{'OK' if ok else 'FAIL'}] import {name}")
        else:
            ok, err = import_file(file_path, f"ci_smoke_file_{idx}")
            print(f"[{'OK' if ok else 'FAIL'}] import file:{file_path}")
        if not ok:
            print("  Error:", err)
            failed += 1

    if failed:
        print(f"{failed} import(s) failed."); return 1
    print("All imports succeeded."); return 0

if __name__ == "__main__":
    raise SystemExit(main())

