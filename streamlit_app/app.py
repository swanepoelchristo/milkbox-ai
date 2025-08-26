import streamlit as st

# -------------------------
# Milkbox AI Dashboard v1
# -------------------------

st.set_page_config(
    page_title="Milkbox AI",
    page_icon="🥛",
    layout="wide"
)

# Title
st.title("🥛 Milkbox AI Dashboard")
st.write("Welcome to the prototype shelf for Milkbox AI tools.")

# Layout – 3 main sections
col1, col2, col3 = st.columns([2, 1, 1])

# -------------------------
# Tools Section
# -------------------------
with col1:
    st.header("🛠️ Tools Shelf")
    st.write("Here you’ll see available AI tools.")
    st.button("📄 CV Builder")
    st.button("🧾 Invoice Generator")
    st.button("🐖 Bush Pig Tool")
    st.button("🍹 Bar Menu Writer")

# -------------------------
# Settings Section
# -------------------------
with col2:
    st.header("⚙️ Settings")
    st.checkbox("Enable English")
    st.checkbox("Enable Afrikaans")
    st.selectbox("Theme", ["Light", "Dark", "Auto"])

# -------------------------
# Status Section
# -------------------------
with col3:
    st.header("📊 Status")
    st.metric("Users Online", 5, delta=+2)
    st.metric("Tools Loaded", 4)
    st.success("System Running")

# -------------------------
# Footer
# -------------------------
st.markdown("---")
st.caption("Milk Roads AI © 2025 | Prototype build")
