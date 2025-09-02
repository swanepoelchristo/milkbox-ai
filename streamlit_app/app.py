from __future__ import annotations

from typing import Any, Dict, List, Optional
import sys
from pathlib import Path
import json

import streamlit as st
import yaml

from utils.tool_loader import render_or_placeholder

# ─────────────────────────────────────────────────────────
# Importer banner + build meta (safe even if file missing)
# ─────────────────────────────────────────────────────────
try:
    st.sidebar.caption("Importer v2 active")
    meta_path = Path(__file__).parent / ".build-meta.json"
    sha = "unknown"
    ts = "unknown"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        sha = (meta.get("sha") or "unknown")[:7]
        ts = meta.get("ts") or "unknown"
    st.sidebar.caption(f"Build: {sha} @ {ts} UTC")
except Exception:
    pass

# ─────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────
APP_ROOT = Path(__file__).resolve().parent              # .../streamlit_app
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
    Use the robust loader:
    - Try import by module path
    - Fallback to streamlit_app/tools/<key>.py
    - If not present, show a friendly placeholder
    - Enforce zero-arg render() when present
    """
    if not key:
        st.header("Milkbox AI Toolbox")
        st.write("Select a tool from the sidebar to begin.")
        return

    entry = next((t for t in tools if t["key"] == key), None)
    if not entry:
        st.error(f"Tool '{key}' not found in tools.yaml.")
        return

    render_or_placeholder(entry["key"], entry["module"])

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
