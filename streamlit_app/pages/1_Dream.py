import streamlit as st
from pathlib import Path

# Path to logo
LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"

# Page config
st.set_page_config(page_title="Dream | MilkBox AI", page_icon="🌙", layout="wide")

# Show logo
st.image(str(LOGO_PATH), width=200)

# Title + intro
st.title("🌙 Dream Page")
st.markdown("Welcome to the Dream cockpit of **MilkBox AI**. Here you can explore new ideas and projects.")

# Example sections
st.subheader("✨ Start a New Dream")
st.text_input("Give your dream a name...", "")

st.subheader("📋 Your Dream List")
st.write("No dreams yet — start by adding one above!")
