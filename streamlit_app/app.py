import streamlit as st

st.set_page_config(page_title="Milkbox AI", page_icon="🥛", layout="wide")

st.title("🥛 Milkbox AI Dashboard")
st.write("Welcome to Milkbox AI – your shelf of smart tools.")

# Placeholder sections
st.header("📂 Tool Shelf")
st.info("Here we'll list tools like CV Maker, Invoice Generator, Bar Menu Writer, etc.")

st.header("⚙️ Settings")
st.write("Admin login, user options, and more will go here.")

st.header("🚀 Status")
st.success("App deployed successfully. Ready for next features!")
