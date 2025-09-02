from __future__ import annotations
import sys, inspect, importlib, importlib.util
from pathlib import Path
import streamlit as st

APP_DIR = Path(__file__).resolve().parents[1]        # .../streamlit_app
TOOLS_DIR = APP_DIR / "tools"

def _ensure_app_on_syspath():
    s = str(APP_DIR)
    if s not in sys.path:
        sys.path.insert(0, s)

def safe_import_module(key: str, module_path: str):
    """
    Try normal import; on ModuleNotFoundError, fall back to loading
    streamlit_app/tools/<key>.py. Return a module or None (if not found).
    Never raises for the 'not present' case.
    """
    _ensure_app_on_syspath()
    try:
        return importlib.import_module(module_path)
    except ModuleNotFoundError:
        candidate = TOOLS_DIR / f"{key}.py"
        if not candidate.exists():
            return None
        try:
            spec = importlib.util.spec_from_file_location(f"_tool_{key}", candidate)
            if spec is None or spec.loader is None:
                return None
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            return mod
        except Exception:
            # If the file exists but is broken, let render_or_placeholder report the error
            raise
    except Exception:
        # Other import errors: bubble up so we can show a clear message
        raise

def render_or_placeholder(key: str, module_path: str):
    """
    If the tool exists and has a zero-arg render(), call it.
    Otherwise show a friendly placeholder (non-fatal).
    """
    try:
        mod = safe_import_module(key, module_path)
    except Exception as e:
        st.error(f"Couldn’t load tool **{key}** (`{module_path}`): {e}")
        return

    if mod is None:
        st.info(
            f"**{key}** isn’t deployed on this branch yet.\n\n"
            f"Expected module: `{module_path}` or file: `streamlit_app/tools/{key}.py`.\n\n"
            "You can keep using the app; this room will light up after the next deploy."
        )
        return

    fn = getattr(mod, "render", None)
    if not callable(fn):
        st.error(f"Tool **{key}** is missing a callable `render()`.")
        return

    sig = inspect.signature(fn)
    required = [
        p for p in sig.parameters.values()
        if p.default is inspect._empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    ]
    if required:
        st.error(
            f"Tool **{key}** `render()` must take **no required args** "
            f"(found: {', '.join(p.name for p in required)})."
        )
        return

    fn()
