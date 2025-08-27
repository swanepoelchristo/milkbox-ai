import streamlit as st

def render():
    st.header("🧾 CV / Resume Builder")
    st.caption("Quickly draft a clean CV from structured inputs. Export coming soon.")

    with st.form("cv_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            location = st.text_input("Location")
        with col2:
            title = st.text_input("Professional title", value="Product Manager")
            website = st.text_input("Website / Portfolio")
            linkedin = st.text_input("LinkedIn")
            github = st.text_input("GitHub")

        st.subheader("Summary")
        summary = st.text_area("Short professional summary", height=110)

        st.subheader("Skills (comma separated)")
        skills = st.text_input("e.g. Python, SQL, Streamlit, Product Strategy, Roadmaps")

        st.subheader("Experience (bullet lines)")
        exp = st.text_area("One bullet per line (STAR format encouraged)", height=140)

        st.subheader("Education")
        education = st.text_area("School, Degree, Years", height=90)

        submitted = st.form_submit_button("Preview CV")

    if not submitted:
        st.info("Fill the form and click **Preview CV**.")
        return

    # Render a simple preview
    st.divider()
    st.subheader("📄 Preview")

    st.markdown(f"### {full_name or 'Your Name'} — {title or ''}".strip(" —"))
    left, right = st.columns([2,1])
    with left:
        st.write(location)
        if website: st.write(website)
    with right:
        st.write(email)
        st.write(phone)
        if linkedin: st.write(linkedin)
        if github: st.write(github)

    if summary:
        st.markdown("#### Summary")
        st.write(summary)

    if skills:
        st.markdown("#### Skills")
        bullets = [s.strip() for s in skills.split(",") if s.strip()]
        st.write(", ".join(bullets))

    if exp:
        st.markdown("#### Experience")
        bullets = [b.strip() for b in exp.split("\n") if b.strip()]
        for b in bullets:
            st.markdown(f"- {b}")

    if education:
        st.markdown("#### Education")
        st.write(education)

    st.success("✅ CV preview generated. (Export to PDF/DOCX can be added next.)")
