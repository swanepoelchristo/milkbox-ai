import importlib
from pathlib import Path
import yaml
import streamlit as st

# ---------- load tool config ----------
CONFIG_PATH = Path(__file__).resolve().parent.parent / "tools.yaml"

@st.cache_data(show_spinner=False)
def load_tools_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    tools = data.get("tools", [])
    norm = []
    for t in tools:
        norm.append({
            "key": t.get("key"),
            "label": t.get("label") or t.get("key", "Untitled"),
            "module": t.get("module"),
        })
    return norm

def load_tool_module(module_path: str):
    try:
        return importlib.import_module(module_path)
    except Exception as e:
        st.error(f"Failed to import `{module_path}`: {e}")
        return None

def render_tool(module):
    render_fn = getattr(module, "render", None)
    if callable(render_fn):
        render_fn()
    else:
        st.warning("This tool does not define a `render()` function.")

# ---------- UI ----------
st.set_page_config(page_title="Milkbox AI Toolbox", page_icon="🍨", layout="wide")

st.sidebar.title("Milkbox AI")
st.sidebar.caption("Toolbox")

tools = load_tools_config()
if not tools:
    st.error("No tools found in `tools.yaml`.")
else:
    labels = [t["label"] for t in tools]
    choice = st.sidebar.selectbox("Select a tool", labels, index=0)
    current = tools[labels.index(choice)]

    st.sidebar.markdown("---")
    st.sidebar.caption(f"Key: `{current['key']}`")
    st.sidebar.caption(f"Module: `{current['module']}`")

    mod = load_tool_module(current["module"])
    if mod:
        render_tool(mod)

