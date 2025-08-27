import os
import importlib
from typing import List, Dict

import streamlit as st
import yaml

# ─────────────────────────────────────────────────────────
# Config / Secrets
# ─────────────────────────────────────────────────────────
PAID_PIN = os.getenv("PAID_PIN", "")  # set in Streamlit → Settings → Secrets

# ─────────────────────────────────────────────────────────
# Load tools.yaml
# ─────────────────────────────────────────────────────────
def load_tools() -> List[Dict]:
    try:
        with open("tools.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        return cfg.get("tools", [])
    except FileNotFoundError:
        st.sidebar.error("tools.yaml not found at project root.")
        return []
    except Exception as e:
        st.sidebar.error(f"Failed to read tools.yaml: {e}")
        return []

TOOLS = load_tools()

# ─────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────
if "paid_unlocked" not in st.session_state:
    st.session_state.paid_unlocked = False
if "selected_tool_key" not in st.session_state:
    st.session_state.selected_tool_key = None  # store the tool.key we opened

# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
def is_allowed(tool: Dict) -> bool:
    tier = (tool.get("tier") or "free").strip().lower()
    if tier == "free":
        return True
    return st.session_state.paid_unlocked

def split_tools_by_tier(tools: List[Dict]):
    free, paid = [], []
    for t in tools:
        (paid if (t.get("tier", "free").lower() == "paid") else free).append(t)
    return free, paid

def open_tool(tool_key: str):
    st.session_state.selected_tool_key = tool_key

# ─────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────
def render_sidebar(tools: List[Dict]):
    st.sidebar.markdown("### 🔓 Access")
    if not st.session_state.paid_unlocked:
        pin_val = st.sidebar.text_input("Enter PIN to unlock paid tools", type="password", placeholder="••••")
        if st.sidebar.button("Unlock"):
            if pin_val and pin_val == PAID_PIN:
                st.session_state.paid_unlocked = True
                st.sidebar.success("Paid tools unlocked")
            else:
                st.sidebar.error("Wrong PIN")
    else:
        st.sidebar.success("Paid tools unlocked")
        if st.sidebar.button("Lock again"):
            st.session_state.paid_unlocked = False

    visible = [t for t in tools if is_allowed(t)]
    free, paid = split_tools_by_tier(visible)

    st.sidebar.markdown("### 🧰 Tools")
    def render_group(header: str, group_tools: List[Dict]):
        if not group_tools:
            return
        st.sidebar.markdown(f"**{header}**")
        for t in group_tools:
            st.sidebar.markdown(f"**{t.get('label','(no label)')}**")
            if t.get("desc"):
                st.sidebar.caption(t["desc"])
            if st.sidebar.button(f"Open: {t.get('label','Open')}", key=f"open_{t.get('key','_')}"):
                open_tool(t.get("key"))

    render_group("Free", free)
    if paid:
        render_group("Pro", paid)

    if st.sidebar.button("🏠 Home"):
        st.session_state.selected_tool_key = None

# ─────────────────────────────────────────────────────────
# Home grid (cards)
# ─────────────────────────────────────────────────────────
def render_home_grid(tools: List[Dict]):
    st.title("Milkbox AI")
    st.caption("Pick a tool to get started. Pro tools unlock with a PIN in the sidebar.")

    visible = [t for t in tools if is_allowed(t)]
    if not visible:
        st.info("No tools available. Unlock paid tools or check tools.yaml.")
        return

    # group free / pro visually
    free, paid = split_tools_by_tier(visible)

    def tool_card(t: Dict):
        st.markdown(f"**{t.get('label','(no label)')}**")
        if t.get("desc"):
            st.caption(t["desc"])
        st.button("Open", key=f"home_open_{t.get('key','_')}", on_click=open_tool, args=(t.get("key"),))
        st.markdown("---")

    def render_grid(group_label: str, group_tools: List[Dict]):
        if not group_tools:
            return
        st.subheader(group_label)
        # 3 columns grid
        cols = st.columns(3)
        for idx, t in enumerate(group_tools):
            with cols[idx % 3]:
                tool_card(t)

    render_grid("Free tools", free)
    render_grid("Pro tools", paid)

# ─────────────────────────────────────────────────────────
# Render selected tool
# ─────────────────────────────────────────────────────────
def render_selected_tool(tools: List[Dict]):
    key = st.session_state.selected_tool_key
    if not key:
        render_home_grid(tools)
        return

    tool = next((t for t in tools if t.get("key") == key), None)
    if not tool:
        st.error(f"Tool not found: {key}")
        return
    if not is_allowed(tool):
        st.error("This tool is locked. Unlock paid tools in the sidebar to continue.")
        return

    module_path = tool.get("module")
    label = tool.get("label", key)
    if not module_path:
        st.error(f"Tool '{label}' is missing a module path.")
        return

    st.markdown(f"## {label}")
    try:
        mod = importlib.import_module(f"streamlit_app.{module_path}")  # e.g. "tools.invoice_gen"
        if hasattr(mod, "render"):
            mod.render()
        else:
            st.error(f"Tool '{label}' does not expose a render() function.")
    except Exception as e:
        st.exception(e)

# ─────────────────────────────────────────────────────────
# Page layout
# ─────────────────────────────────────────────────────────
st.set_page_config(page_title="Milkbox AI", page_icon="🧰", layout="wide")
render_sidebar(TOOLS)
render_selected_tool(TOOLS)
