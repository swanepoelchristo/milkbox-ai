import streamlit as st

def render():
    st.header("Resume Builder")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full name")
        title = st.text_input("Title", placeholder="e.g., Data Analyst")
        email = st.text_input("Email")
        phone = st.text_input("Phone")
    with col2:
        city = st.text_input("City")
        country = st.text_input("Country")
        website = st.text_input("Website / LinkedIn")

    st.subheader("Summary")
    summary = st.text_area("Short professional summary")

    st.subheader("Experience")
    exp = st.text_area("Experience (markdown)", height=150,
                       placeholder="- Company A — Role (2022–now)\n  - Did X\n  - Did Y")

    st.subheader("Education")
    edu = st.text_area("Education (markdown)",
                       placeholder="- Degree — University (Year)")

    if st.button("Preview resume"):
        st.success("Preview below ⬇️")
        st.markdown(f"## {name}")
        st.write(title or "")
        st.write(f"{email} | {phone} | {city}, {country} | {website}")
        st.markdown("---")
        st.markdown(f"### Summary\n{summary}")
        st.markdown(f"### Experience\n{exp}")
        st.markdown(f"### Education\n{edu}")
