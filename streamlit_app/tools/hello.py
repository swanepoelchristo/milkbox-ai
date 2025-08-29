# streamlit_app/tools/hello.py
import streamlit as st
from components.reg_watch import render_reg_watch

def render():
    st.title("🧰 Milkbox AI Toolbox")
    st.subheader("Hello & About")
    st.write(
        "Welcome! This is your central hub for Milkbox AI tools. "
        "Pick a tool from the left sidebar to get started."
    )

    with st.expander("About this prototype", expanded=False):
        st.markdown(
            """
            - Tools are loaded dynamically from **tools.yaml**.
            - Each page follows a simple `render()` convention.
            - We've added a shared **Regulatory Watch** card so you can keep an eye on standards updates from anywhere.
            """
        )

    st.divider()
    render_reg_watch("🔎 Regulatory Watch")
