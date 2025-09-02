#!/usr/bin/env python3
"""
Smoke-check tool modules defined in tools.yaml.

Accepted tools.yaml shapes:
1) Mapping:
   tools:
     hello: tools.hello
     notes:
       module: tools.notes
       enabled: true
2) List of {key, module[, enabled]}:
   tools:
     - key: hello
       module: tools.hello
     - key: notes
       module: tools.notes
       enabled: true
3) List of single-key maps:
   tools:
     - hello: tools.hello
     - notes: tools.notes

Behavior:
- Adds streamlit_app to sys.path so 'tools.*' resolves.
- Import module; on ModuleNotFoundError, fall back to streamlit_app/tools/<key>.py.
- If neither path exists, SKIP (planned/not present) – non-blocking.
- If module/file exists, require a zero-arg callable render(); otherwise FAIL.
- Honors enabled:false (skips).
"""

from __future__ import annotations
import sys
import inspect
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Tuple, List

try:
    import yaml  # type: ignore
except ModuleNotFoundError:
    print("::error::PyYAML is required (pip install pyyaml).")
    sys.exit(1)

REPO_ROOT = Path(__file__).resolve().parents[1]
STREAMLIT_APP_DIR = REPO_ROOT / "streamlit_app"
TOOLS_DIR = STREAMLIT_APP_DIR / "tools"
TOOLS_YAML = REPO_ROOT / "tools.yaml"


def _ensure_streamlit_stub():
    """Provide a minimal 'streamlit' stub so tools can import in CI without the dependency."""
    try:
        import streamlit  # noqa: F401
    except ModuleNotFoundError:
        class _StreamlitStub:
            def __getattr__(self, _name):
                def _fn(*_args, **_kwargs):
                    return None
                return _fn
        sys.modules["streamlit"] = _StreamlitStub()


def _add_entry(out: Dict[str, Dict[str, object]], key: str, module: str | None, enabled: object = True):
    # default module path if omitted: tools.<key>
    mod = module or f"tools.{key}"
    out[key] = {"module": str(mod), "enabled": bool(enabled)}


def _load_tools_entries() -> Dict[str, Dict[str, object]]:
    if not TOOLS_YAML.exists():
        print(f"::error file=tools.yaml::Missing tools.yaml at {TOOLS_YAML}")
        sys.exit(1)
    try:
        data = yaml.safe_load(TOOLS_YAML.read_text()) or {}
    except Exception as e:
        print(f"::error file=tools.yaml::Failed to parse tools.yaml: {e}")
        sys.exit(1)

    candidate = data.get("tools", data)
    result: Dict[str, Dict[str, object]] = {}

    if isinstance(candidate, dict):
        # form: {hello: "tools.hello"} or {hello: {module: "...", enabled: bool}}
        for key, val in candidate.items():
            if isinstance(val, str):
                _add_entry(result, key, val, True)
            elif isinstance(val, dict):
                _add_entry(result, key, val.get("module"), val.get("enabled", True))
            elif val is None:
                _add_entry(result, key, None, True)
            else:
                print(f"::warning file=tools.yaml::Skipping '{key}' – unsupported value type {type(val).__name__}.")
    elif isinstance(candidate, list):
        # forms:
        #  - {key: "hello", module: "tools.hello", enabled: true}
        #  - {"hello": "tools.hello"} (single-key map)
        #  - "hello" (string -> default to tools.hello)
        for i, item in enumerate(candidate):
            if isinstance(item, str):
                _add_entry(result, item, None, True)
                continue
            if isinstance(item, dict):
                if "key" in item:
                    _add_entry(result, str(item["key"]), item.get("module"), item.get("enabled", True))
                    continue
                if len(item) == 1:
                    k, v = next(iter(item.items()))
                    if isinstance(v, str):
                        _add_entry(result, str(k), v, True)
                    elif isinstance(v, dict):
                        _add_entry(result, str(k), v.get("module"), v.get("enabled", True))
                    else:
                        print(f"::warning file=tools.yaml::Skipping list item {i} – unsupported single-key value.")
                    continue
                print(f"::warning file=tools.yaml::Skipping list item {i} – missing 'key' or single-key mapping.")
                continue
            print(f"::warning file=tools.yaml::Skipping list item {i} – unsupported type {type(item).__name__}.")
    else:
        print("::error file=tools.yaml::'tools' must be a mapping or a list of tool entries.")
        sys.exit(1)

    if not result:
        print("::error file=tools.yaml::No usable tool entries found.")
        sys.exit(1)
    return result


def _import_module_primary(module_path: str):
    s = str(STREAMLIT_APP_DIR)
    if s not in sys.path:
        sys.path.insert(0, s)
    return importlib.import_module(module_path)


def _import_module_fallback(key: str):
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


def main() -> int:
    _ensure_streamlit_stub()
    entries = _load_tools_entries()

    failures: List[str] = []
    successes: List[str] = []
    skips: List[str] = []

    for key, cfg in entries.items():
        module_path = str(cfg.get("module"))
        enabled = bool(cfg.get("enabled", True))
        if not enabled:
            print(f"::notice::{key}: SKIP (enabled=false) (module='{module_path}')")
            skips.append(key)
            continue

        try:
            try:
                mod = _import_module_primary(module_path)
            except ModuleNotFoundError:
                try:
                    mod = _import_module_fallback(key)
                except FileNotFoundError:
                    print(f"SKIP {key:<12} {module_path} -> not present (no module or file)")
                    print(f"::notice::{key}: SKIP (not present) (module='{module_path}')")
                    skips.append(key)
                    continue

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
