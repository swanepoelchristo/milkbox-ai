from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import importlib
import importlib.util
import sys
from pathlib import Path
import types

import streamlit as st
import yaml


# ─────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────
APP_ROOT = Path(__file__).resolve().parent              # .../streamlit_app
TOOLS_DIR = APP_ROOT / "tools"                          # .../streamlit_app/tools
REPO_ROOT = APP_ROOT.parent                             # repo root
TOOLS_FILE = REPO_ROOT / "tools.yaml"                   # .../tools.yaml

# Make sure the app can import from streamlit_app/
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


# ─────────────────────────────────────────────────────────
# Config loading
# ─────────────────────────────────────────────────────────
def load_tools_config() -> Dict[str, Any]:
    """
    Read tools.yaml from the repo root and return the parsed dict.

    Expected shape:
      tools:
        - key: invoice_gen
          label: Invoice Generator
          module: tools.invoice_gen
          section: Free
          description: ...
    """
    try:
        with TOOLS_FILE.open("r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except FileNotFoundError as e:
        st.error(
            f"Failed to read {TOOLS_FILE.relative_to(REPO_ROOT)}: {e}\n\n"
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
        label = (str(t.get("label", key)).strip() or key) if key else key
        section = t.get("section")
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


# ─────────────────────────────────────────────────────────
# Smart importer
# ─────────────────────────────────────────────────────────
CANDIDATE_FILES = [
    "__init__.py",
    "app.py",
    "main.py",
    "index.py",
    "page.py",
    "render.py",
]

def _load_module_from_file(fully_qualified_name: str, file_path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(fully_qualified_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to create spec for {file_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[fully_qualified_name] = mod
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


def smart_import(module_path: str) -> Tuple[Optional[types.ModuleType], List[Path]]:
    """
    Try importlib first. If that fails, try loading from the filesystem so
    packages without __init__.py or directory-only tools still work.

    Returns (module or None, tried_paths)
    """
    tried: List[Path] = []
    # 1) Normal import
    try:
        return importlib.import_module(module_path), tried
    except ModuleNotFoundError:
        pass
    except Exception:
        # Unexpected import error; let caller handle so we can show it.
        return None, tried

    # Expecting tools.<name>
    parts = module_path.split(".")
    if len(parts) != 2 or parts[0] != "tools":
        # Not our domain—give up here.
        return None, tried

    name = parts[1]

    # a) tools/<name>.py
    single_file = TOOLS_DIR / f"{name}.py"
    tried.append(single_file)
    if single_file.exists():
        try:
            return _load_module_from_file(module_path, single_file), tried
        except Exception:
            return None, tried

    # b) tools/<name>/(candidates)
    pkg_dir = TOOLS_DIR / name
    if pkg_dir.is_dir():
        for fname in CANDIDATE_FILES + [f"{name}.py"]:
            candidate = pkg_dir / fname
            tried.append(candidate)
            if candidate.exists():
                try:
                    return _load_module_from_file(module_path, candidate), tried
                except Exception:
                    return None, tried

    return None, tried


# ─────────────────────────────────────────────────────────
# Sidebar UI
# ─────────────────────────────────────────────────────────
def render_sidebar(tools: List[Dict[str, Any]]) -> Optional[str]:
    """
    Render a grouped sidebar if 'section' is present in the YAML.
    Falls back to a single list otherwise. Returns the selected tool key.
    """
    st.sidebar.title("Milkbox AI Toolbox")

    if not tools:
        st.sidebar.info("No tools found in tools.yaml.")
        return None

    selected_key = st.session_state.get("selected_tool")
    has_sections = any(t.get("section") for t in tools)

    if has_sections:
        # Group by 'section' while keeping insertion order
        groups: Dict[str, List[Dict[str, Any]]] = {}
        for t in tools:
            groups.setdefault(t.get("section") or "Tools", []).append(t)

        for sec_name, items in groups.items():
            st.sidebar.markdown(f"### {sec_name}")
            for t in items:
                if st.sidebar.button(f"Open: {t['label']}", key=f"btn_{t['key']}"):
                    selected_key = t["key"]
    else:
        labels = [t["label"] for t in tools]
        keys = [t["key"] for t in tools]
        default_index = keys.index(selected_key) if selected_key in keys else 0
        idx = st.sidebar.radio(
            "Choose a tool",
            options=list(range(len(keys))),
            format_func=lambda i: labels[i],
            index=default_index,
        )
        selected_key = keys[idx]

    st.session_state["selected_tool"] = selected_key
    return selected_key


# ─────────────────────────────────────────────────────────
# Main area
# ─────────────────────────────────────────────────────────
def render_selected_tool(tools: List[Dict[str, Any]], key: Optional[str]) -> None:
    """
    Import and render the selected tool.

    We keep using the module path provided by tools.yaml (e.g. "tools.notes").
    If the normal import fails, we fall back to loading directly from the
    filesystem so directory-only tools work without __init__.py.
    """
    if not key:
        st.header("Milkbox AI Toolbox")
        st.write("Select a tool from the sidebar to begin.")
        return

    # Lookup in config
    entry = next((t for t in tools if t["key"] == key), None)
    if not entry:
        st.error(f"Tool '{key}' not found in tools.yaml.")
        return

    module_path = entry["module"]

    # Try smart import
    mod, tried = smart_import(module_path)
    if mod is None:
        # Generate a helpful message
        rel = [p.relative_to(REPO_ROOT) if p.is_absolute() else p for p in tried]
        tried_lines = "\n".join(f"• {p}" for p in rel) or "• (no candidates found)"
        st.error(
            f"Couldn't import module `{module_path}`.\n\n"
            f"Make sure the module path in tools.yaml matches the file on disk.\n"
            f"Tried the following paths:\n{tried_lines}"
        )
        return

    # Render
    if hasattr(mod, "render"):
        try:
            mod.render()
        except Exception as e:
            st.error(f"Error while rendering `{entry['label']}`: {e}")
    else:
        st.error(f"Module `{module_path}` has no function `render()`.")


# ─────────────────────────────────────────────────────────
# App entrypoint
# ─────────────────────────────────────────────────────────
def main() -> None:
    st.set_page_config(page_title="Milkbox AI Toolbox", layout="wide")

    cfg = load_tools_config()
    tools = normalize_tools(cfg)

    selected = render_sidebar(tools)
    render_selected_tool(tools, selected)


if __name__ == "__main__":
    main()

