import importlib
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st
import yaml

# ─────────────────────────────────────────────────────────
# Paths / config
# ─────────────────────────────────────────────────────────
TOOLS_FILE = Path(__file__).resolve().parent / "tools.yaml"


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
def import_tool_module(module_path: str):
    """
    Try importing a tool module using both absolute and package-qualified names.
    Supports both:
      - tools.invoice_gen
      - streamlit_app.tools.invoice_gen
    """
    if not module_path:
        raise ModuleNotFoundError("Empty module path")

    candidates = []
    if module_path.startswith("streamlit_app."):
        candidates = [module_path, module_path.replace("streamlit_app.", "", 1)]
    else:
        candidates = [f"streamlit_app.{module_path}", module_path]

    last_err = None
    for name in candidates:
        try:
            return importlib.import_module(name)
        except ModuleNotFoundError as e:
            last_err = e
    # If both attempts fail, re-raise the last error
    raise last_err


def load_config() -> Dict[str, Any]:
    """Load tools.yaml; return {} if missing/empty."""
    if not TOOLS_FILE.exists():
        return {}
    with open(TOOLS_FILE, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except Exception as e:
            st.error(f"YAML parse error in tools.yaml: {e}")
            return {}


def normalize_tools(cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Return a normalized list of tools."""
    raw = cfg.get("tools", []) or []
    tools: List[Dict[str, Any]] = []
    for t in raw:
        if not isinstance(t, dict):
            continue
        key = t.get("key")
        label = t.get("label", key or "Unnamed")
        module = t.get("module")
        tier = (t.get("tier") or "free").strip().lower()
        desc = t.get("desc", "")
        if key and module:
            tools.append(
                {"key": key, "label": label, "module": module, "tier": tier, "desc": desc}
            )
    return tools


def sidebar_home_button():
    st.sidebar.markdown("### ")
    if st.sidebar.button("🏠 Home", use_container_width=True):
        st.session_state["selected_tool"] = None


def render_sidebar(tools: List[Dict[str, Any]]):
    """Build the grouped sidebar with buttons."""
    st.sidebar.title("CV Builder")
    st.sidebar.caption("International CV builder with import-from-file and DOCX/PDF exports.")
    if st.sidebar.button("Open: CV Builder", use_container_width=True):
        st.session_state["selected_tool"] = "cv_builder"

    st.sidebar.markdown("---")
    st.sidebar.title("Bar Tools (ABV & Tips)")
    st.sidebar.caption("Quick ABV/pure alcohol calculator and tip/bill splitter.")
    if st.sidebar.button("Open: Bar Tools (ABV & Tips)", use_container_width=True):
        st.session_state["selected_tool"] = "bar_tools"

    st.sidebar.markdown("---")
    st.sidebar.title("Pro")
    st.sidebar.caption("International CV Builder (Pro)\n\nPro templates, locale rules, advanced formatting, and premium exports.")
    if st.sidebar.button("Open: International CV Builder (Pro)", use_container_width=True):
        st.session_state["selected_tool"] = "cv_builder"

    # Generic grouped list below (in case you add many more)
    st.sidebar.markdown("---")

    groups = {
        "free": {"title": "Free tools"},
        "paid": {"title": "Pro tools"},
        "pro": {"title": "Pro tools"},  # accept "pro" as an alias
    }
    # Order: free → paid
    tiers_in_order = ["free", "paid"]

    # Index by key for screenshots/links
    idx_by_key = {t["key"]: t for t in tools}

    for tier in tiers_in_order:
        entries = [t for t in tools if (t.get("tier") or "free").lower() in (tier, "pro" if tier == "paid" else tier)]
        if not entries:
            continue

        st.sidebar.subheader(groups[tier]["title"])
        for t in entries:
            btn_label = f"Open: {t['label']}"
            if st.sidebar.button(btn_label, use_container_width=True, key=f"btn_{t['key']}"):
                st.session_state["selected_tool"] = t["key"]

    sidebar_home_button()


def render_home():
    st.title("Milkbox AI Toolbox")
    st.markdown("""
Welcome 👋  
This is your hub for Milkbox tools. Use the sidebar to open a tool.

**Highlights**
- **International CV Builder (Pro)**: Import an existing CV (PDF/DOCX) or build from scratch; export to DOCX/PDF.
- **Bar Tools (ABV & Tips)**: Quick ABV/pure alcohol calculator and a tip/bill splitter.

You can add new tools or update existing ones with the **Tool Builder**.
    """)


def render_selected_tool(tools: List[Dict[str, Any]]):
    sel_key = st.session_state.get("selected_tool")
    if not sel_key:
        render_home()
        return

    tool = next((t for t in tools if t["key"] == sel_key), None)
    if not tool:
        st.error(f"Tool '{sel_key}' not found in tools.yaml")
        return

    # Header area
    st.title(tool["label"])
    if tool.get("desc"):
        st.caption(tool["desc"])

    # Safe import + render
    try:
        module_path = tool["module"]
        mod = import_tool_module(module_path)
        if not hasattr(mod, "render"):
            st.error(f"Module '{module_path}' has no function 'render()'.")
            return
        mod.render()
    except Exception as e:
        st.error(f"Failed to load tool: {e}")


def main():
    st.set_page_config(page_title="Milkbox AI Toolbox", layout="wide")
    cfg = load_config()
    tools = normalize_tools(cfg)

    # Ensure state exists
    if "selected_tool" not in st.session_state:
        st.session_state["selected_tool"] = None

    # Sidebar
    render_sidebar(tools)

    # Main view
    render_selected_tool(tools)


if __name__ == "__main__":
    main()
