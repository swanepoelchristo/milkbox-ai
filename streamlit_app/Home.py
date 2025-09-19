import streamlit as st

# --- Page config ---
st.set_page_config(page_title="MilkBox AI", layout="wide")

# --- Header ---
st.title("🏠 Home")
st.write("Welcome to **MilkBox AI** — your cockpit dashboard.")

# --- Navigation links to pages ---
st.page_link("pages/1_Dream.py", label="🚀 Open Dream", icon="✨")
st.page_link("pages/2_War_Room.py", label="🛡️ Open War Room", icon="🧭")

# --- Status ---
st.success("Home loaded ✅")
