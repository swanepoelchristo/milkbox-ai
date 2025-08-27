import importlib
from pathlib import Path
import yaml
import streamlit as st

# ─────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────
TOOLS_FILE = Path(__file__).resolve().parent / "tools.yaml"


# ─────────────────────────────────────────────────────────
# YAML loading
# ─────────────────────────────────────────────────────────
def load_tools():
    try:
        with open(TOOLS_FILE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        tools = cfg.get("tools", []) or []
        # Normalize: keep only dicts with at least a key + module
        normalized = []
        for t in tools:
            if isinstance(t, dict) and t.get("key") and t.get("module"):
                normalized.append(t)
        return normalized
    except Exception as e:
        st.error(f"Failed to read tools.yaml: {e}")
        return []


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
def _find_tool_by_key(tools, key: str):
    for t in tools:
        if t.get("key") == key:
            return t
    return None


def _module_importable(mod_path: str) -> bool:
    """
    Returns True if module 'streamlit_app.<mod_path>' can be imported, else False.
    """
    try:
        importlib.import_module(f"streamlit_app.{mod_path}")  # e.g., "tools.invoice_gen"
        return True
    except Exception:
        return False


def _get_tool_if_ready(tools, key: str):
    """
    Returns the tool dict if (a) key exists in yaml and (b) module is importable.
    Otherwise returns None.
    """
    t = _find_tool_by_key(tools, key)
    if not t:
        return None
    mod_path = t.get("module", "")
    if not mod_path:
        return None
    return t if _module_importable(mod_path) else None


def _select_tool(tool_key: str):
    """
    Persist selection in session and rerun.
    """
    st.session_state["selected_tool_key"] = tool_key
    st.rerun()


def render_selected_tool(tool_dict: dict):
    """
    Safely import and render the selected tool.
    """
    module_path = tool_dict.get("module")
    label = tool_dict.get("label", tool_dict.get("key", "Tool"))

    try:
        module = importlib.import_module(f"streamlit_app.{module_path}")
    except Exception as e:
        st.error(
            f"Could not import module for **{label}** "
            f"(`streamlit_app.{module_path}`):\n\n{e}"
        )
        return

    if not hasattr(module, "render"):
        st.error(f"Module `{module_path}` has no `render()` function.")
        return

    try:
        module.render()
    except Exception as e:
        st.error(f"Error while rendering **{label}**: {e}")


# ─────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────
def render_sidebar(tools_list):
    st.sidebar.header("CV Builder")
    st.sidebar.caption("International CV builder with import-from-file and DOCX/PDF exports.")

    t = _get_tool_if_ready(tools_list, "cv_builder")
    if t and st.sidebar.button("Open: CV Builder", use_container_width=True):
        _select_tool(t["key"])

    st.sidebar.header("Bar Tools (ABV & Tips)")
    st.sidebar.caption("Quick ABV/pure alcohol calculator and tip/bill splitter.")

    t = _get_tool_if_ready(tools_list, "bar_tools")
    if t and st.sidebar.button("Open: Bar Tools (ABV & Tips)", use_container_width=True):
        _select_tool(t["key"])

    st.sidebar.header("Pro")
    st.sidebar.caption(
        "International CV Builder (Pro)\n\nPro templates, locale rules, advanced formatting, and premium exports."
    )

    t = _get_tool_if_ready(tools_list, "cv_builder_pro")
    if t and st.sidebar.button("Open: International CV Builder (Pro)", use_container_width=True):
        _select_tool(t["key"])

    st.sidebar.divider()
    if st.sidebar.button("🏡 Home", use_container_width=True):
        st.session_state.pop("selected_tool_key", None)
        st.rerun()

    # Optional: quick access to all available tools (debug/utility)
    with st.sidebar.expander("All tools", expanded=False):
        for t in tools_list:
            key = t["key"]
            label = t.get("label", key)
            mod = t["module"]
            ok = _module_importable(mod)
            col1, col2 = st.columns([1, 1])
            with col1:
                st.write(f"• {label}")
            with col2:
                if ok:
                    if st.button(f"Open", key=f"open_{key}"):
                        _select_tool(key)
                else:
                    st.caption("not installed")


def render_home():
    st.title("Milkbox AI Toolbox")
    st.write("Welcome! Pick a tool from the left, or choose one below.")

    # Example: show a small grid of ready tools (from YAML)
    tools_list = load_tools()
    ready = [t for t in tools_list if _module_importable(t["module"])]
    if ready:
        st.subheader("Available tools")
        for t in ready:
            st.markdown(f"- **{t.get('label', t['key'])}** — `{t['key']}`")


def main():
    st.set_page_config(page_title="Milkbox AI Toolbox", layout="wide")
    tools_list = load_tools()

    # Sidebar
    render_sidebar(tools_list)

    # Main panel — render selected tool or home
    selected_key = st.session_state.get("selected_tool_key")
    if selected_key:
        tool = _find_tool_by_key(tools_list, selected_key)
        if tool:
            st.title(tool.get("label", selected_key))
            render_selected_tool(tool)
        else:
            st.error(f"Selected tool `{selected_key}` not found in tools.yaml.")
            render_home()
    else:
        render_home()


if __name__ == "__main__":
    main()

