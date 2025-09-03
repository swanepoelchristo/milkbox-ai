import streamlit as st

def render():
    st.header("📝 Notes")
    st.caption("First draft of notes. Build here.")

    text = st.text_area("Write your notes", height=240, placeholder="Type here...")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save"):
            # Placeholder only — no persistence yet
            st.success("Saved (placeholder).")
    with col2:
        if st.button("Clear"):
            st.experimental_rerun()
