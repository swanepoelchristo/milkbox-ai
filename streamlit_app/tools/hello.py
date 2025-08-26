import streamlit as st

def render():
    st.header("Hello 👋")
    name = st.text_input("Your name", value="world")
    if st.button("Say hello"):
        st.success(f"Hello, **{name}**! 👋 Nice to meet you.")
    with st.expander("About this tool"):
        st.write("This is a friendly starter tool used to verify the dynamic loader works.")
