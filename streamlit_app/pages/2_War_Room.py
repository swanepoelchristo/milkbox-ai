import streamlit as st
from pathlib import Path

# Path to logo
LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"

# Page config
st.set_page_config(page_title="War Room | MilkBox AI", page_icon="🛡️", layout="wide")

# Show logo
st.image(str(LOGO_PATH), width=200)

# Title + intro
st.title("🛡️ War Room")
st.markdown("Welcome to the **War Room** cockpit of MilkBox AI — track missions, manage tools, and review progress.")

# Example sections
st.subheader("📊 Active Missions")
st.write("No missions yet — create one to begin!")

st.subheader("📂 Logs & Activity")
st.write("Logs will appear here once you start running tools.")
