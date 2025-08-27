import os
import importlib
from typing import List, Dict

import streamlit as st
import yaml

# ─────────────────────────────────────────────────────────
# Config / Secrets
# Set PAID_PIN in Streamlit → App → Settings → Secrets
# ─────────────────────────────────────────────────────────
PAID_PIN = os.getenv("PAID_PIN", "")  # e.g. "2468"


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
    free = []
    paid = []
    for t in tools:
        (paid if (t.get("tier", "free").lower() == "paid") else free).append(t)
    return free, paid


def open_tool(tool_key: str):
    st.session_state.selected_tool_key = tool_key


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

    # Visible tools after gating
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
            # "Open" button uses the tool key in the button key to be unique
            if st.sidebar.button(f"Open: {t.get('label','Open')}", key=f"open_{t.get('key','_')}"):
                open_tool(t.get("key"))

    # Free group
    render_group("Free", free)
    # Paid group (only shows if unlocked or no PIN set)
    if paid:
        render_group("Pro", paid)

    # Home link
    if st.sidebar.button("🏠 Home"):
        st.session_state.selected_tool_key = None


def render_selected_tool(tools: List[Dict]):
    key = st.session_state.selected_tool_key
    if not key:
        # Home view
        st.title("Milkbox AI")
        st.write("Select a tool from the left to get started.")
        return

    # Find the tool by key among *all* tools (not only visible), but enforce gating.
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
        # Example module path: "tools.invoice_gen" → import "streamlit_app.tools.invoice_gen"
        mod = importlib.import_module(f"streamlit_app.{module_path}")
        if hasattr(mod, "render"):
            mod.render()
        else:
            st.error(f"Tool '{label}' does not expose a render() function.")
    except Exception as e:
        st.exception(e)


# ─────────────────────────────────────────────────────────
# Page layout
# ─────────────────────────────────────────────────────────
st.set_page_config(page_title="Milkbox AI", page_icon="🧰", layout="centered")
render_sidebar(TOOLS)
render_selected_tool(TOOLS)

