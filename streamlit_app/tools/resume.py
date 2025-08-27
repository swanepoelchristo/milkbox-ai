import streamlit as st

def render():
    st.header("📝 Resume Builder")

    with st.form("resume_form", clear_on_submit=False):
        name = st.text_input("Name")
        email = st.text_input("Email")
        role = st.text_input("Desired Role")
        summary = st.text_area("Professional Summary")
        submitted = st.form_submit_button("Generate preview")

        if submitted:
            st.divider()
            st.subheader("Preview")
            st.markdown(f"**{name}** · {email}")
            st.markdown(f"**Role:** {role}")
            st.write(summary or "_No summary provided_")
