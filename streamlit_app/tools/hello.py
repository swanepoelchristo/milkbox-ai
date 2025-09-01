import streamlit as st

TOOL_NAME = "Hello"

def render():
    st.title("👋 Hello Tool")
    st.success("Importer v2 path is live. This is the first draft of `hello`.\n\nBuild your UI here.")
    st.caption("Tip: Each tool lives at streamlit_app/tools/<name>.py and must expose render().")
