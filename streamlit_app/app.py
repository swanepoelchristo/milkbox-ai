import streamlit as st

st.set_page_config(page_title="Milkbox Streamlit", page_icon="🍼")
st.title("🍼 Milkbox Streamlit Starter")
st.write("Hello! This is your Streamlit starter app.")

name = st.text_input("Your name", "world")
if st.button("Say hello"):
    st.success(f"Hello, {name}!")
