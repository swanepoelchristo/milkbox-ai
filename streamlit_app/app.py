import streamlit as st

st.set_page_config(page_title="Milkbox AI Toolbox", page_icon="🧰", layout="wide")

# Sidebar for tool selection
st.sidebar.title("🧰 Milkbox Toolbox")
tool = st.sidebar.selectbox(
    "Choose a tool",
    ["Hello & About", "Resume Builder", "Notes"]
)

# Tool: Hello & About
if tool == "Hello & About":
    st.title("👋 Hello & About")
    st.write("Welcome to **Milkbox AI**, your lightweight AI toolbox.")
    name = st.text_input("Your name", "world")
    if st.button("Say hello"):
        st.success(f"Hello, {name}! 👋")
    st.markdown("---")
    st.subheader("About")
    st.write("Milkbox AI is a lightweight toolbox. This prototype includes Hello, Resume Builder, and Notes.")

# Tool: Resume Builder
elif tool == "Resume Builder":
    st.title("📄 Resume Builder")
    st.write("This is where the resume builder logic will go.")
    name = st.text_input("Full Name")
    role = st.text_input("Role")
    summary = st.text_area("Summary")
    if st.button("Generate Resume"):
        st.success(f"Generated resume for {name}, {role}.")

# Tool: Notes
elif tool == "Notes":
    st.title("📝 Notes")
    st.write("Simple notes section to test input/output.")
    note = st.text_area("Write your note here")
    if st.button("Save Note"):
        st.success("Note saved (in memory for now).")
