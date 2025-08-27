import streamlit as st
import yaml
import importlib
from pathlib import Path

# Load tool definitions from tools.yaml
TOOLS_FILE = Path(__file__).resolve().parent.parent / "tools.yaml"

def load_tools():
    with open(TOOLS_FILE, "r") as f:
        config = yaml.safe_load(f)
    return config.get("tools", [])

def main():
    st.set_page_config(page_title="Milkbox AI Toolbox", layout="wide")
    st.title("🧰 Milkbox AI Toolbox")

    tools = load_tools()
    menu = {tool["label"]: tool for tool in tools}
    choice = st.sidebar.radio("Choose a tool", list(menu.keys()))

    selected_tool = menu[choice]
    module_path = selected_tool["module"]
    try:
        module = importlib.import_module(module_path)
        module.render()
    except Exception as e:
        st.error(f"Failed to load tool: {e}")

if __name__ == "__main__":
    main()
