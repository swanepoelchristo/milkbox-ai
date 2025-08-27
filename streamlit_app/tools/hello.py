import streamlit as st

def render():
    st.header("👋 Hello & About")
    st.write("Welcome to **Milkbox AI**, your lightweight AI toolbox.")

    with st.form("hello_form", clear_on_submit=False):
        name = st.text_input("Your name", value="world")
        submitted = st.form_submit_button("Say hello")
        if submitted:
            st.success(f"Hello, **{name}**! 👋")

    st.divider()
    st.subheader("About")
    st.write(
        "This prototype includes a dynamic tool menu loaded from `tools.yaml`. "
        "Adding a new tool file + yaml entry makes it appear automatically."
    )
