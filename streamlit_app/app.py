# --- Add these imports at the top if missing ---
import os
import yaml
import importlib
import streamlit as st

# --- Load tools.yaml as before ---
with open("tools.yaml", "r", encoding="utf-8") as f:
    cfg = yaml.safe_load(f) or {}
TOOLS = cfg.get("tools", [])

# --- Simple unlock state ---
if "paid_unlocked" not in st.session_state:
    st.session_state.paid_unlocked = False

# --- Sidebar unlock UI ---
with st.sidebar:
    st.markdown("### 🔓 Access")
    if not st.session_state.paid_unlocked:
        pin = st.text_input("Enter PIN to unlock paid tools", type="password", placeholder="••••")
        if st.button("Unlock"):
            if pin and pin == os.getenv("PAID_PIN", ""):
                st.session_state.paid_unlocked = True
                st.success("Paid tools unlocked")
            else:
                st.error("Wrong PIN")
    else:
        st.success("Paid tools unlocked")
        if st.button("Lock again"):
            st.session_state.paid_unlocked = False

# --- Filter tools by tier ---
def is_allowed(tool: dict) -> bool:
    tier = (tool.get("tier") or "free").strip().lower()
    if tier == "free":
        return True
    return st.session_state.paid_unlocked

VISIBLE_TOOLS = [t for t in TOOLS if is_allowed(t)]

# --- Sidebar tool list ---
st.sidebar.markdown("### 🧰 Tools")
labels = [t["label"] for t in VISIBLE_TOOLS]
selected = st.sidebar.selectbox("Select a tool", labels) if labels else None

# --- Render selected tool ---
if selected:
    t = next(tool for tool in VISIBLE_TOOLS if tool["label"] == selected)
    module_path = t["module"]  # e.g., "tools.invoice_gen"
    try:
        mod = importlib.import_module(f"streamlit_app.{module_path}")
        # convention: every tool exposes render()
        if hasattr(mod, "render"):
            mod.render()
        else:
            st.error(f"Tool '{t['label']}' is missing a render() function.")
    except Exception as e:
        st.exception(e)
else:
    st.title("Milkbox AI")
    st.write("Select a tool from the left to get started.")
