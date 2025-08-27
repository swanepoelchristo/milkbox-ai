import importlib
from pathlib import Path
from typing import List, Dict, Any

import streamlit as st
import yaml

APP_TITLE = "Milkbox AI Toolbox"
TOOLS_CONFIG = Path(__file__).resolve().parents[1] / "tools.yaml"


@st.cache_data(show_spinner=False)
def load_tools_config() -> List[Dict[str, Any]]:
    if not TOOLS_CONFIG.exists():
        return []
    with TOOLS_CONFIG.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    tools = data.get("tools", [])
    # minimal validation
    cleaned = []
    for t in tools:
        if isinstance(t, dict) and "label" in t and "module" in t:
            cleaned.append(t)
    return cleaned


def import_renderer(module_path: str):
    """
    Import module and return its `render` function.
    We expect each tool module to define a `render()` callable.
    """
    mod = importlib.import_module(module_path)
    if not hasattr(mod, "render"):
        raise AttributeError(f"Module '{module_path}' has no function 'render()'.")
    return getattr(mod, "render")


def main():
    st.set_page_config(page_title=APP_TITLE, page_icon="🍦", layout="wide")
    st.title(APP_TITLE)

    tools = load_tools_config()
    if not tools:
        st.warning("No tools found. Check `tools.yaml`.")
        st.stop()

    # Sidebar menu
    labels = [t["label"] for t in tools]
    choice = st.sidebar.selectbox("Tools", labels, index=0)

    # Find chosen tool
    selected = next(t for t in tools if t["label"] == choice)

    # Render chosen tool from its module
    try:
        render = import_renderer(selected["module"])
        render()
    except Exception as e:
        st.error(f"Failed to load tool '{selected['label']}': {e}")
        st.exception(e)


if __name__ == "__main__":
    main()
