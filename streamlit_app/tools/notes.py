import streamlit as st

def render():
    st.title("📝 Notes")
    st.caption("First draft of notes. Build here.")

    # ensure the key exists once
    st.session_state.setdefault("notes", "")

    st.text_area(
        "Write your notes",
        key="notes",
        height=250,
        placeholder="Type here..."
    )

    if st.button("Save"):
        st.success("Saved in session (persists until the app restarts).")
