import streamlit as st

def render():
    st.header("🗒 Notes")

    if "notes" not in st.session_state:
        st.session_state["notes"] = []

    new_note = st.text_area("Write a note", "")
    if st.button("Save note"):
        if new_note.strip():
            st.session_state["notes"].append(new_note.strip())
            st.success("Note saved!")
        else:
            st.warning("Empty note not saved.")

    st.divider()
    st.subheader("Saved Notes")
    if st.session_state["notes"]:
        for i, note in enumerate(st.session_state["notes"], start=1):
            st.markdown(f"**{i}.** {note}")
    else:
        st.info("No notes yet. Add one above!")
