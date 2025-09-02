#!/usr/bin/env python3
"""
Smoke-check tool modules defined in tools.yaml.

- Reads tools.yaml mapping {key -> module} or {key: {module: "..."}}, with or without a top-level 'tools:'.
- Adds streamlit_app to sys.path so 'tools.*' resolves.
- Tries to import the module; on ModuleNotFoundError falls back to streamlit_app/tools/<key>.py.
- If neither import path exists, we SKIP (planned/not present yet) with a GA notice.
- If we import a module, we REQUIRE a zero-arg callable render(); otherwise it's a failure.
- Exits non-zero only if any *present* tool fails. Skips do not fail CI.

This lets you keep future/planned tools in tools.yaml without blocking PRs.
"""

from __future__ import annotations
import sys
import inspect
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Tuple, List

# --- deps ---------------------------------------------------------------

try:
    import yaml  # type: ignore
except ModuleNotFoundError:
    print("::error::PyYAML is required (pip install pyyaml).")
    sys.exit(1)

# --- paths --------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_APP_DIR = REPO_ROOT / "streamlit_app"
TOOLS_DIR = STREAMLIT_APP_DIR / "tools"
TOOLS_YAML = REPO_ROOT / "tools.yaml"

# --- helpers ------------------------------------------------------------

def _ensure_streamlit_stub():
    """Provide a minimal 'streamlit' stub so tools can import without the heavy dep in CI."""
    try:
        import streamlit  # noqa: F401
    except ModuleNotFoundError:
        class _StreamlitStub:
            def __getattr__(self, _name):
                def _fn(*_args, **_kwargs):
                    return None
                return _fn
        sys.modules["streamlit"] = _StreamlitStub()


def _load_tools_map() -> Dict[str, str]:
    if not TOOLS_YAML.exists():
        print(f"::error file=tools.yaml::Missing tools.yaml at {TOOLS_YAML}")
        sys.exit(1)
    try:
        data = yaml.safe_load(TOOLS_YAML.read_text()) or {}
    except Exception as e:
        print(f"::error file=tools.yaml::Failed to parse tools.yaml: {e}")
        sys.exit(1)

    candidate = data.get("tools", data)
    if not isinstance(candidate, dict):
        print("::error file=tools.yaml::Expected a mapping of tool entries.")
        sys.exit(1)

    result: Dict[str, str] = {}
    for key, val in candidate.items():
        if isinstance(val, str):
            result[key] = val
        elif isinstance(val, dict) and isinstance(val.get("module"), str):
            result[key] = val["module"]
        else:
            print(f"::warning file=tools.yaml::Skipping '{key}' – no 'module' string found.")
    if not result:
        print("::error file=tools.yaml::No usable (key -> module) entries.")
        sys.exit(1)
    return result


def _import_module_primary(module_path: str):
    # Ensure 'streamlit_app' is on sys.path so 'tools.*' is importable
    s = str(STREAMLIT_APP_DIR)
    if s not in sys.path:
        sys.path.insert(0, s)
    return importlib.import_module(module_path)


def _import_module_fallback(key: str):
    # Load from file streamlit_app/tools/<key>.py
    candidate = TOOLS_DIR / f"{key}.py"
    if not candidate.exists():
        raise FileNotFoundError(f"Fallback file not found: {candidate}")
    spec = importlib.util.spec_from_file_location(f"_smokeload_{key}", candidate)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not create spec for {candidate}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[assignment]
    return mod


def _validate_render(mod, key: str) -> Tuple[bool, str]:
    fn = getattr(mod, "render", None)
    if not callable(fn):
        return False, f"{key}: Missing callable render()"
    try:
        sig = inspect.signature(fn)
        required_positional = [
            p for p in sig.parameters.values()
            if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            and p.default is inspect._empty
        ]
        if required_positional:
            names = ", ".join(p.name for p in required_positional)
            return False, f"{key}: render() must take no required positional args (found: {names})"
    except Exception as e:
        return False, f"{key}: Could not inspect render(): {e}"
    return True, f"{key}: OK"


# --- main ---------------------------------------------------------------

def main() -> int:
    _ensure_streamlit_stub()
    tools_map = _load_tools_map()

    failures: List[str] = []
    successes: List[str] = []
    skips: List[str] = []

    for key, module_path in tools_map.items():
        try:
            try:
                # 1) primary import
                mod = _import_module_primary(module_path)
            except ModuleNotFoundError:
                # 2) fallback: file streamlit_app/tools/<key>.py
                try:
                    mod = _import_module_fallback(key)
                except FileNotFoundError:
                    # Neither module nor file exists -> SKIP (planned/not present)
                    print(f"SKIP {key:<12} {module_path} -> not present (no module or file)")
                    print(f"::notice::{key}: SKIP (not present) (module='{module_path}')")
                    skips.append(key)
                    continue

            # 3) validate render() if module exists
            ok, msg = _validate_render(mod, key)
            if ok:
                print(f"OK   {key:<12} {module_path}")
                print(f"::notice::{msg} (module='{module_path}')")
                successes.append(key)
            else:
                print(f"BAD  {key:<12} {module_path} -> {msg}")
                print(f"::error::{msg} (module='{module_path}')")
                failures.append(msg)

        except Exception as e:
            # Any other import error (SyntaxError, ImportError inside module, etc.) is a failure
            print(f"BAD  {key:<12} {module_path} -> {e!r}")
            print(f"::error::{key}: Import check failed for '{module_path}': {e!r}")
            failures.append(f"{key}: {e!r}")

    if failures:
        print(f"\nFAILED tools: {len(failures)}")
        for f in failures:
            print(f" - {f}")
        return 1

    print(f"All present tools passed: {len(successes)} OK; {len(skips)} SKIPPED (not present)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
