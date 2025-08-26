import streamlit as st

def render():
    st.header("👋 Hello & About")
    st.write("Welcome to **Milkbox AI**, your lightweight AI toolbox.")

    name = st.text_input("Your name", value="world")
    if st.button("Say hello"):
        st.success(f"Hello, {name}!")

    st.subheader("About")
    st.write(
        "Milkbox AI is a lightweight toolbox. "
        "This prototype includes Hello, Resume Builder, and Notes."
    )
