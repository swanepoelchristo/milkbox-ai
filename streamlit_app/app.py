# streamlit_app/app.py

from __future__ import annotations  # stop runtime eval of hints
from typing import Any, Dict, List, Optional
import sys
from pathlib import Path

import streamlit as st
import yaml
import importlib
import importlib.util
from types import ModuleType

# --- Ensure "tools.*" imports resolve ---
APP_ROOT = Path(__file__).resolve().parent  # .../streamlit_app
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
# ----------------------------------------

# ─────────────────────────────────────────────────────────
# Config
# tools.yaml lives at the REPO ROOT (not inside streamlit_app/)
# ─────────────────────────────────────────────────────────
TOOLS_FILE = APP_ROOT.parent / "tools.yaml"

# ─────────────────────────────────────────────────────────
# Helper: resilient importer for tools.*
# ─────────────────────────────────────────────────────────
def import_tool_module(module_path: str) -> Optional[ModuleType]:
    """
    Try normal importlib import; if that fails and module_path starts with
    'tools.', try to load from:
      - streamlit_app/tools/<name>.py
      - streamlit_app/tools/<name>/__init__.py
      - streamlit_app/tools/<name>    (extensionless single file)
    Returns the loaded module or None.
    """
    # 1) Try the standard way first
    try:
        return importlib.import_module(module_path)
    except ModuleNotFoundError:
        pass  # fall through to custom paths
    except Exception:
        # any other import error should bubble up (syntax error, etc.)
        raise

    # 2) Fallbacks for non-standard layouts
    if not module_path.startswith("tools."):
        return None

    name = module_path.split(".", 1)[1]
    base = APP_ROOT / "tools"
    candidates = [
        base / f"{name}.py",
        base / name / "__init__.py",
        base / name,  # extensionless file
    ]
    for p in candidates:
        if p.exists():
            spec = importlib.util.spec_from_file_location(module_path, p)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                sys.modules[module_path] = mod
                spec.loader.exec_module(mod)  # type: ignore[attr-defined]
                return mod
    return None

# ─────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────
def load_tools_config() -> Dict[str, Any]:
    """
    Read tools.yaml from the repo root and return the parsed dict.
    Expected structure:
      tools:
        - key: invoice_gen
          label: Invoice Generator
          module: tools.invoice_gen
          section: Free
          description: ...
    """
    try:
        with open(TOOLS_FILE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except FileNotFoundError as e:
        st.error(
            f"Failed to read tools.yaml: {e}\n\n"
            "Make sure tools.yaml is at the repository root."
        )
        return {"tools": []}
    except Exception as e:
        st.error(f"Error parsing tools.yaml: {e}")
        return {"tools": []}
    return cfg

def normalize_tools(raw: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a list of tool dicts with safe defaults."""
    items = raw.get("tools", []) or []
    cleaned: List[Dict[str, Any]] = []
    for t in items:
        if not isinstance(t, dict):
            continue
        key = str(t.get("key", "")).strip()
        module = str(t.get("module", "")).strip()
        label = str(t.get("label", key)).strip() or key
        section = t.get("section")  # optional
        description = t.get("description", "")

        if key and module:
            cleaned.append(
                {
                    "key": key,
                    "label": label,
                    "module": module,
                    "section": section,
                    "description": description,
                }
            )
    return cleaned

def tool_by_key(tools: List[Dict[str, Any]], key: str) -> Optional[Dict[str, Any]]:
    for t in tools:
        if t["key"] == key:
            return t
    return None

# ─────────────────────────────────────────────────────────
# Sidebar UI
# ─────────────────────────────────────────────────────────
def render_sidebar(tools: List[Dict[str, Any]]) -> Optional[str]:
    """
    Render a grouped sidebar if 'section' is present in YAML.
    Falls back to a single list otherwise.
    Returns the selected tool key.
    """
    st.sidebar.title("Milkbox AI Toolbox")

    if not tools:
        st.sidebar.info("No tools found in tools.yaml.")
        return None

    # Decide grouping
    has_sections = any(t.get("section") for t in tools)
    selected_key = st.session_state.get("selected_tool")

    if has_sections:
        # Group by 'section' while keeping insertion order
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for t in tools:
            sec = t.get("section") or "Tools"
            groups.setdefault(sec, []).append(t)

        for sec_name, items in groups.items():
            st.sidebar.markdown(f"### {sec_name}")
            for t in items:
                if st.sidebar.button(f"Open: {t['label']}", key=f"btn_{t['key']}"):
                    selected_key = t["key"]
    else:
        # Simple radio list
        labels = [t["label"] for t in tools]
        keys = [t["key"] for t in tools]
        default_index = 0
        if selected_key in keys:
            default_index = keys.index(selected_key)
        idx = st.sidebar.radio(
            "Choose a tool",
            options=list(range(len(keys))),
            format_func=lambda i: labels[i],
            index=default_index,
        )
        selected_key = keys[idx]

    # Persist selection
    st.session_state["selected_tool"] = selected_key
    return selected_key

# ─────────────────────────────────────────────────────────
# Main area
# ─────────────────────────────────────────────────────────
def render_selected_tool(tools: List[Dict[str, Any]], key: Optional[str]) -> None:
    """
    Import and render the selected tool.

    NOTE: We import EXACTLY what the YAML specifies in 'module'
    (e.g., 'tools.invoice_gen'). The importer is forgiving and
    supports .py files, package dirs, and extensionless single files.
    """
    if not key:
        st.header("Milkbox AI Toolbox")
        st.write("Select a tool from the sidebar to begin.")
        return

    t = tool_by_key(tools, key)
    if not t:
        st.error(f"Tool '{key}' not found in tools.yaml")
        return

    module_path = t["module"]
    try:
        mod = import_tool_module(module_path)
    except Exception as e:
        st.error(f"Error importing `{module_path}`: {e}")
        return

    if not mod:
        # Give a helpful hint about what was tried.
        name = module_path.split(".", 1)[1] if module_path.startswith("tools.") else module_path
        base = APP_ROOT / "tools"
        tried = [
            str(base / f"{name}.py"),
            str(base / name / "__init__.py"),
            str(base / name),
        ]
        st.error(
            "Couldn't import module `{}`.\n\n"
            "Make sure the module path in tools.yaml matches the file on disk.\n"
            "Tried the following paths:\n- {}".format(module_path, "\n- ".join(tried))
        )
        return

    # Render
    if hasattr(mod, "render"):
        try:
            mod.render()
        except Exception as e:
            st.error(f"Error while rendering `{t['label']}`: {e}")
    else:
        st.error(f"Module `{module_path}` has no function `render()`.")

# ─────────────────────────────────────────────────────────
# App entrypoint
# ─────────────────────────────────────────────────────────
def main():
    st.set_page_config(page_title="Milkbox AI Toolbox", layout="wide")
    cfg = load_tools_config()
    tools = normalize_tools(cfg)
    selected = render_sidebar(tools)
    render_selected_tool(tools, selected)

if __name__ == "__main__":
    main()
