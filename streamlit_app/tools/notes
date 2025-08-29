import streamlit as st

def render():
    st.header("📝 Notes")

    if "notes" not in st.session_state:
        st.session_state.notes = ""

    st.text_area(
        "Write your notes",
        key="notes",
        height=250,
        placeholder="Type here..."
    )

    if st.button("Save"):
        st.success("Saved in session (persists until the app restarts).")

    st.caption("Tip: this simple demo stores notes in session_state.")
