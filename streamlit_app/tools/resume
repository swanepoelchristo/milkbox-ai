import streamlit as st

def render():
    st.header("📄 Resume Builder")

    with st.form("resume_form", clear_on_submit=False):
        name = st.text_input("Full name", placeholder="Jane Doe")
        email = st.text_input("Email", placeholder="jane@doe.com")
        role = st.text_input("Desired role", placeholder="Product Manager")
        summary = st.text_area("Professional summary", height=160)
        submitted = st.form_submit_button("Generate preview")

    if submitted:
        st.divider()
        st.subheader("Preview")
        st.markdown(f"### {name or 'Your Name'} · {email or 'email@example.com'}")
        st.markdown(f"**{role or 'Role'}**")
        st.write(summary or "_No summary provided_")
