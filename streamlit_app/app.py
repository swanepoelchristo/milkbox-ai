import io
import textwrap
import streamlit as st

st.set_page_config(page_title="Milkbox AI", page_icon="🍦", layout="centered")

# --- Sidebar ---
with st.sidebar:
    st.image("https://static.streamlit.io/examples/cat.jpg", caption="Milkbox AI (prototype)")
    st.markdown("**Version:** 0.1.0\n\n**Status:** prototype")

st.title("🍦 Milkbox AI")
st.caption("Prototype utilities – no external APIs required")

tab1, tab2, tab3 = st.tabs(["Hello & About", "Resume Builder", "Notes"])

# --- Tab 1: Hello & About ---
with tab1:
    st.subheader("Hello 👋")
    name = st.text_input("Your name", value="christo", key="hello_name")
    if st.button("Say hello"):
        st.success(f"Hello, **{name}**! Milkbox is alive. ✅")

    st.divider()
    st.subheader("About")
    st.markdown(
        """
        **Milkbox AI** is a lightweight toolbox.  
        This prototype includes:
        - A *Resume Builder* that turns form fields into a clean Markdown summary
        - A *Notes* pad that keeps text during your session
        - Zero external services, so deploys fast on Streamlit Cloud

        When we’re happy with UX, we’ll wire real models & move to Bluehost.
        """
    )

# --- Tab 2: Resume Builder ---
with tab2:
    st.subheader("Resume Builder (Markdown)")

    with st.form("resume_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            full_name = st.text_input("Full name", value="Chris Example")
            email = st.text_input("Email", value="chris@example.com")
            phone = st.text_input("Phone", value="+1 555 123 4567")
        with col2:
            role = st.text_input("Target role", value="Operations Manager")
            location = st.text_input("Location", value="Cape Town, ZA")
            website = st.text_input("Website / LinkedIn", value="linkedin.com/in/chris")

        st.markdown("**Summary**")
        summary = st.text_area(
            "One-paragraph pitch",
            value="Operations leader with 8+ years experience improving processes, reducing costs, and leading cross-functional teams."
        )

        st.markdown("**Experience**")
        jobs = []
        for i in range(1, 3 + 1):
            with st.expander(f"Job #{i}", expanded=(i == 1)):
                company = st.text_input(f"Company #{i}", value=f"Company {i}")
                title = st.text_input(f"Title #{i}", value="Operations Lead")
                dates = st.text_input(f"Dates #{i}", value="2019–2023")
                bullets = st.text_area(
                    f"Highlights #{i} (one per line)",
                    value="• Led team of 12\n• Cut costs by 18%\n• Built weekly ops dashboard"
                )
                jobs.append((company, title, dates, bullets))

        submitted = st.form_submit_button("Generate Resume")
        if submitted:
            # Build Markdown
            md_lines = [
                f"# {full_name}",
                f"{role} · {location} · {email} · {phone} · {website}",
                "",
                "## Summary",
                summary,
                "",
                "## Experience",
            ]
            for (company, title, dates, bullets) in jobs:
                if any([company, title, dates, bullets]):
                    md_lines += [
                        f"### {title} — {company}",
                        f"*{dates}*",
                        "",
                        *[line.strip() for line in bullets.splitlines() if line.strip()],
                        ""
                    ]

            resume_md = "\n".join(md_lines).strip()

            st.success("Resume generated ✅")
            st.markdown(resume_md)

            # Download button
            buf = io.BytesIO(resume_md.encode("utf-8"))
            st.download_button(
                "Download as Markdown",
                data=buf,
                file_name=f"{full_name.replace(' ', '_')}_resume.md",
                mime="text/markdown"
            )

# --- Tab 3: Notes (session-persistent) ---
with tab3:
    st.subheader("Notes")
    default_text = textwrap.dedent("""
    - Draft ideas here
    - Paste snippets you want to keep while working
    - This persists for your session only
    """).strip()

    if "notes_text" not in st.session_state:
        st.session_state.notes_text = default_text

    st.session_state.notes_text = st.text_area(
        "Your notes",
        value=st.session_state.notes_text,
        height=240
    )
    st.info("Notes are stored in session and will reset when you close the app session.")
