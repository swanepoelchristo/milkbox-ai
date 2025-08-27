import streamlit as st

def render():
    st.header("📝 Notes")
    st.caption("Simple local notes (session only).")
    notes = st.session_state.setdefault("notes", [])
    with st.form("notes_form", clear_on_submit=True):
        text = st.text_area("Add a note", height=120)
        add = st.form_submit_button("Add note")
    if add and text.strip():
        notes.append(text.strip())
    if notes:
        st.subheader("Your notes")
        for i, n in enumerate(notes, 1):
            st.markdown(f"{i}. {n}")
    else:
        st.info("No notes yet. Add your first note above.")
