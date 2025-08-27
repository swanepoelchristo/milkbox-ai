import io
from datetime import datetime
from typing import List, Dict

import streamlit as st

# ---------------------------------------------------------
# Small helpers
# ---------------------------------------------------------
def _lines(text: str) -> List[str]:
    """Normalize comma- or newline-separated input → list of non-empty trimmed lines."""
    if not text:
        return []
    if "," in text and "\n" not in text:
        parts = [p.strip() for p in text.split(",")]
    else:
        parts = [p.strip() for p in text.splitlines()]
    return [p for p in parts if p]

def _md_section(title: str, items: List[str]) -> str:
    if not items:
        return ""
    out = [f"## {title}"]
    out += [f"- {x}" for x in items]
    out.append("")  # blank line
    return "\n".join(out)

def _md_header(name: str, title: str, contact: Dict[str, str]) -> str:
    lines = [f"# {name or 'Your Name'}"]
    if title.strip():
        lines.append(f"**{title.strip()}**")
    parts = []
    if contact.get("email"):   parts.append(f"📧 {contact['email']}")
    if contact.get("phone"):   parts.append(f"📞 {contact['phone']}")
    if contact.get("website"): parts.append(f"🌐 {contact['website']}")
    if contact.get("linkedin"):parts.append(f"🔗 {contact['linkedin']}")
    if contact.get("github"):  parts.append(f"🐙 {contact['github']}")
    if parts:
        lines.append(" | ".join(parts))
    lines.append("")  # blank
    return "\n".join(lines)

def _to_markdown(name, title, contact, summary, skills, experience, education) -> str:
    md = []
    md.append(_md_header(name, title, contact))
    if summary.strip():
        md += ["## Summary", summary.strip(), ""]
    md.append(_md_section("Skills", skills))
    md.append(_md_section("Experience", experience))
    md.append(_md_section("Education", education))
    return "\n".join([x for x in md if x is not None])

# ---------------------------------------------------------
# DOCX export (python-docx)
# ---------------------------------------------------------
def build_docx(name, title, contact, summary, skills, experience, education) -> bytes:
    from docx import Document
    from docx.shared import Pt, Inches

    doc = Document()
    # Title
    head = doc.add_heading(level=0)
    run = head.add_run(name or "Your Name")
    run.font.size = Pt(20)

    if title.strip():
        p = doc.add_paragraph()
        r = p.add_run(title.strip())
        r.bold = True

    # Contact
    parts = []
    if contact.get("email"):   parts.append(f"Email: {contact['email']}")
    if contact.get("phone"):   parts.append(f"Phone: {contact['phone']}")
    if contact.get("website"): parts.append(f"Website: {contact['website']}")
    if contact.get("linkedin"):parts.append(f"LinkedIn: {contact['linkedin']}")
    if contact.get("github"):  parts.append(f"GitHub: {contact['github']}")
    if parts:
        doc.add_paragraph(" | ".join(parts))

    # Summary
    if summary.strip():
        doc.add_heading("Summary", level=1)
        doc.add_paragraph(summary.strip())

    # Skills
    if skills:
        doc.add_heading("Skills", level=1)
        for s in skills:
            doc.add_paragraph(s, style="List Bullet")

    # Experience
    if experience:
        doc.add_heading("Experience", level=1)
        for x in experience:
            doc.add_paragraph(x, style="List Bullet")

    # Education
    if education:
        doc.add_heading("Education", level=1)
        for e in education:
            doc.add_paragraph(e, style="List Bullet")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

# ---------------------------------------------------------
# PDF export (ReportLab)
# ---------------------------------------------------------
def build_pdf(name, title, contact, summary, skills, experience, education) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
    from reportlab.lib.units import mm

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    H1 = styles["Heading1"]; H2 = styles["Heading2"]; Body = styles["BodyText"]
    # Slightly smaller body for CV density
    Body.fontSize = 10
    Body.leading = 14

    story = []

    # Header
    story.append(Paragraph(name or "Your Name", H1))
    if title.strip():
        story.append(Paragraph(title.strip(), H2))

    contact_parts = []
    if contact.get("email"):   contact_parts.append(contact["email"])
    if contact.get("phone"):   contact_parts.append(contact["phone"])
    if contact.get("website"): contact_parts.append(contact["website"])
    if contact.get("linkedin"):contact_parts.append(contact["linkedin"])
    if contact.get("github"):  contact_parts.append(contact["github"])
    if contact_parts:
        story.append(Paragraph(" | ".join(contact_parts), Body))
    story.append(Spacer(1, 6))

    # Summary
    if summary.strip():
        story.append(Paragraph("Summary", H2))
        story.append(Paragraph(summary.strip().replace("\n", "<br/>"), Body))
        story.append(Spacer(1, 6))

    # Skills
    if skills:
        story.append(Paragraph("Skills", H2))
        story.append(ListFlowable([ListItem(Paragraph(s, Body)) for s in skills], bulletType="bullet"))
        story.append(Spacer(1, 6))

    # Experience
    if experience:
        story.append(Paragraph("Experience", H2))
        story.append(ListFlowable([ListItem(Paragraph(x, Body)) for x in experience], bulletType="bullet"))
        story.append(Spacer(1, 6))

    # Education
    if education:
        story.append(Paragraph("Education", H2))
        story.append(ListFlowable([ListItem(Paragraph(e, Body)) for e in education], bulletType="bullet"))
        story.append(Spacer(1, 6))

    doc.build(story)
    return buf.getvalue()

# ---------------------------------------------------------
# UI
# ---------------------------------------------------------
def render():
    st.header("📄 CV Builder (Real)")

    with st.form("cv_form", clear_on_submit=False):
        st.subheader("Profile")
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full name", "")
            title = st.text_input("Professional title", "Product Manager")
        with c2:
            email = st.text_input("Email", "")
            phone = st.text_input("Phone", "")

        c3, c4, c5 = st.columns(3)
        with c3:
            website = st.text_input("Website / Portfolio", "")
        with c4:
            linkedin = st.text_input("LinkedIn", "")
        with c5:
            github = st.text_input("GitHub", "")

        st.subheader("Summary")
        summary = st.text_area(
            "Short professional summary",
            placeholder="3–5 lines that capture your strengths, outcomes, and focus."
        )

        st.subheader("Skills (comma-separated or one per line)")
        skills_raw = st.text_area(
            "Skills",
            placeholder="Python, Streamlit, Product Strategy, Stakeholder Management"
        )

        st.subheader("Experience (bullets: one per line)")
        exp_raw = st.text_area(
            "Experience bullets",
            placeholder="Led cross-functional team of 8 to ship onboarding flow increasing activation by 18%.\nBuilt data pipeline reducing reporting time by 60%."
        )

        st.subheader("Education (bullets: one per line)")
        edu_raw = st.text_area(
            "Education bullets",
            placeholder="B.Sc. in Computer Science — University of Cape Town\nProduct Strategy, Reforge (2024)"
        )

        submitted = st.form_submit_button("Preview")

    if not submitted:
        st.info("Fill out your details and click **Preview** to generate your CV.")
        return

    skills = _lines(skills_raw)
    experience = _lines(exp_raw)
    education = _lines(edu_raw)
    contact = {"email": email, "phone": phone, "website": website, "linkedin": linkedin, "github": github}

    # Live preview as Markdown
    st.subheader("Preview")
    md = _to_markdown(name, title, contact, summary, skills, experience, education)
    st.markdown(md)

    # Exports
    today = datetime.now().strftime("%Y-%m-%d")
    base = (name or "resume").strip().lower().replace(" ", "_")
    fn_docx = f"{base}_{today}.docx"
    fn_pdf  = f"{base}_{today}.pdf"

    # DOCX
    try:
        docx_bytes = build_docx(name, title, contact, summary, skills, experience, education)
        st.download_button("⬇️ Download DOCX", data=docx_bytes, file_name=fn_docx, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", use_container_width=True)
    except Exception as e:
        st.warning(f"Could not generate DOCX (python-docx missing?): {e}")

    # PDF
    try:
        pdf_bytes = build_pdf(name, title, contact, summary, skills, experience, education)
        st.download_button("⬇️ Download PDF", data=pdf_bytes, file_name=fn_pdf, mime="application/pdf", use_container_width=True)
    except Exception as e:
        st.warning(f"Could not generate PDF (reportlab missing?): {e}")

# Allow local run: streamlit run streamlit_app/tools/cv_builder.py
if __name__ == "__main__":
    render()
