import streamlit as st
import io
from datetime import datetime
from html import escape

# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------
def norm_multiline(text: str) -> list[str]:
    """
    Split a textarea into non-empty, trimmed lines.
    Accepts comma-separated lists too; we normalize to lines first.
    """
    if not text:
        return []
    # If the user used commas for skills, split on commas first
    if "," in text and "\n" not in text:
        parts = [p.strip() for p in text.split(",")]
    else:
        parts = [p.strip() for p in text.splitlines()]
    return [p for p in parts if p]

def to_markdown(
    name: str,
    title: str,
    email: str,
    phone: str,
    website: str,
    linkedin: str,
    github: str,
    summary: str,
    skills: list[str],
    experience: list[str],
    education: list[str],
) -> str:
    """Build a clean Markdown CV."""
    lines = []
    # Header
    header = name.strip() or "Your Name"
    subtitle = title.strip()
    lines.append(f"# {header}")
    if subtitle:
        lines.append(f"**{subtitle}**")
    lines.append("")

    # Contact
    contact_parts = []
    if email: contact_parts.append(f"📧 {email}")
    if phone: contact_parts.append(f"📞 {phone}")
    if website: contact_parts.append(f"🌐 {website}")
    if linkedin: contact_parts.append(f"🔗 {linkedin}")
    if github: contact_parts.append(f"🐙 {github}")
    if contact_parts:
        lines.append(" | ".join(contact_parts))
        lines.append("")

    # Summary
    if summary.strip():
        lines.append("## Summary")
        lines.append(summary.strip())
        lines.append("")

    # Skills
    if skills:
        lines.append("## Skills")
        for s in skills:
            lines.append(f"- {s}")
        lines.append("")

    # Experience
    if experience:
        lines.append("## Experience")
        for x in experience:
            lines.append(f"- {x}")
        lines.append("")

    # Education
    if education:
        lines.append("## Education")
        for e in education:
            lines.append(f"- {e}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"

def markdown_to_html(md_text: str) -> str:
    """
    Very small HTML wrap for the markdown content.
    We let Streamlit render markdown, but for download we provide
    a simple styled HTML shell so the user can open/print easily.
    (We don't convert md → html here; we embed in <pre> for portability.)
    """
    # Minimal style that prints nicely from the browser.
    style = """
    <style>
      body { max-width: 820px; margin: 2rem auto; font: 16px/1.5 system-ui, Arial, sans-serif; color: #222; }
      h1 { margin-bottom: 0; }
      h2 { margin-top: 1.5rem; }
      pre { white-space: pre-wrap; font: inherit; }
      .meta { color: #444; margin: .3rem 0 1rem; }
      hr { border: 0; border-top: 1px solid #ddd; margin: 1.25rem 0; }
    </style>
    """
    # We keep it super robust: escape() ensures md characters don't break HTML.
    content = escape(md_text)
    html = f"<!DOCTYPE html><html><head><meta charset='utf-8'>{style}</head><body><pre>{content}</pre></body></html>"
    return html

def bytes_file(data: str, encoding="utf-8") -> bytes:
    return data.encode(encoding)


# -------------------------------------------------------------------
# UI
# -------------------------------------------------------------------
def render():
    st.header("🧰 CV Builder")

    with st.form("cv_form", clear_on_submit=False):
        st.subheader("Basic info")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full name", "")
            title = st.text_input("Professional title", "Product Manager")
        with col2:
            email = st.text_input("Email", "")
            phone = st.text_input("Phone", "")

        col3, col4, col5 = st.columns(3)
        with col3:
            website = st.text_input("Website / Portfolio", "")
        with col4:
            linkedin = st.text_input("LinkedIn", "")
        with col5:
            github = st.text_input("GitHub", "")

        st.subheader("Summary")
        summary = st.text_area(
            "Short professional summary",
            placeholder="3–5 lines that capture your value proposition, strengths, and goals."
        )

        st.subheader("Skills")
        skills_raw = st.text_area(
            "Skills (comma-separated or one per line)",
            placeholder="Python, Streamlit, Product Strategy, Stakeholder Management"
        )

        st.subheader("Experience (bullets)")
        experience_raw = st.text_area(
            "List key achievements / roles (one per line)",
            placeholder="Led cross-functional team of 8 to ship new onboarding flow increasing activation by 18%.\nLaunched data pipeline reducing reporting time by 60%."
        )

        st.subheader("Education (bullets)")
        education_raw = st.text_area(
            "Degrees / certificates (one per line)",
            placeholder="B.Sc. in Computer Science — University of Cape Town\nProduct Strategy, Reforge (2024)"
        )

        submitted = st.form_submit_button("Preview CV")

    if submitted:
        skills = norm_multiline(skills_raw)
        experience = norm_multiline(experience_raw)
        education = norm_multiline(education_raw)

        md = to_markdown(
            name=name,
            title=title,
            email=email,
            phone=phone,
            website=website,
            linkedin=linkedin,
            github=github,
            summary=summary,
            skills=skills,
            experience=experience,
            education=education,
        )

        st.subheader("Preview")
        st.markdown(md)

        # Downloads
        today = datetime.now().strftime("%Y-%m-%d")
        safe_name = (name or "resume").strip().lower().replace(" ", "_")
        md_filename = f"{safe_name}_{today}.md"
        html_filename = f"{safe_name}_{today}.html"

        colA, colB = st.columns(2)
        with colA:
            st.download_button(
                "⬇️ Download Markdown",
                data=bytes_file(md),
                file_name=md_filename,
                mime="text/markdown",
                use_container_width=True,
            )
        with colB:
            html_doc = markdown_to_html(md)
            st.download_button(
                "⬇️ Download HTML",
                data=bytes_file(html_doc),
                file_name=html_filename,
                mime="text/html",
                use_container_width=True,
            )


# Allow running locally:  streamlit run streamlit_app/tools/cv_builder.py
if __name__ == "__main__":
    render()

