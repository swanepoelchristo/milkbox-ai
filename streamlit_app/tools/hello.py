import streamlit as st

def render():
    st.header("👋 Hello & About")
    with st.form("hello_form", clear_on_submit=False):
        name = st.text_input("Your name", value="world")
        submitted = st.form_submit_button("Say hello")
    if submitted:
        st.success(f"Hello, **{name}**! 👋")

    st.divider()
    st.subheader("About")
    st.write("This prototype loads tools dynamically from `tools.yaml`.")
